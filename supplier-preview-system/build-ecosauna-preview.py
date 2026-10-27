#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BOUNDED BUILDER — THE ECOSAUNA PRIVATE SUPPLIER PREVIEW · v2, PREMIUM.

v2, 18 October 2026, founder brief "ECOSAUNA SUPPLIER PREVIEW · PREMIUM
VISUAL REDESIGN". v1 (commit afb8e0b) was accurate but looked like the old
supplier-preview shell. v2 keeps every verified fact, every qualification
and every guard, and re-presents them in the newer PlotNua language: A Home
for Art, The Borrowed Garden, the approved editorial homepage and the
Possibility Reveal prototype.

WHAT v2 TAKES FROM THE TEMPLATE, AND WHAT IT DOES NOT.

  TAKEN, VERBATIM: the template's <head> (robots, fonts), its whole
  stylesheet including the generated PLOTNUA UI KIT, and the demonstration
  markup -- the real Results card inside its framed screen. SUPPLIER-
  PREVIEW-SYSTEM-V1 §5 is kept: the supplier still sees themselves inside
  the genuine interface, not a mock.

  REPLACED: the page shell around it (private bar, hero, sections, footer).
  The old shell is the "too traditional" part. The v2 shell is written here,
  scoped under body.ev so it cannot leak into the UI kit.

  CHANGED IN THE DEMONSTRATION, ON FOUNDER INSTRUCTION:
    · the two "#" links. "Explore with EcoSauna" now goes to
      www.ecosauna.ie; "Ask PlotNua" is no longer a control (it is shown as
      an illustrative label with no link, because no such public feature is
      live to link to);
    · the inert Save / Open My Plot / My Plot buttons are marked inert, so
      nothing on the page looks clickable and does nothing;
    · the image position. §10.2 left it as an empty panel with one neutral
      label. The founder judged that unfinished. It now carries an ORIGINAL
      generic line illustration and exactly one caption saying so. No
      rights-process copy (G3d unchanged); the caption states what the
      drawing is, the same convention as the Possibility Reveal's
      "ILLUSTRATION · NOT AN ASSESSMENT".

*** RECONCILIATION, EVIDENCE AND TRAPS: UNCHANGED FROM v1. ***

Atlas ORG-000218 "EcoSauna Ireland" (rec7or5nAX2Z57tiN), reused. Reply of
18 Oct 2026 from ecosauna2022hottub@gmail.com (Gmail 1a14e93ff0d46b6b) is a
request to SEE a preview; nothing else is granted. That the address speaks
for www.ecosauna.ie is AWAITING SUPPLIER CONFIRMATION. Every figure is from
the code www.ecosauna.ie serves (/assets/index-Cy6LUy6E.js), read 18 Oct
2026: the configurator catalogue ("Starting from €…"), its option price
table, and its delivery, base and estimate notices.

  1 · Two sets of starting prices on their own site -> configurator figures,
      labelled, and the question asked.
  2 · VAT not stated -> no VAT basis claimed.
  3 · Testimonials, a planning-exemption statement, health claims and a
      templated track-record line on their site -> none may appear.
  4 · Origin not established; a separate Estonian Ecosauna exists -> no
      origin claim.
  5 · "All 32 counties" -> attributed in their name only.

*** IMAGERY. ***

State C, unchanged: no EcoSauna image anywhere. ECO_IMAGES is empty. v2
also builds the route for the day permission exists, without opening it:
a non-empty ECO_IMAGES is refused unless image-rights-manifest.json carries
a LIVE grant for ecosauna.ie with the exact credit this page prints (the
same register-not-comment rule as the Irish Sauna Company builder), and the
preview-only containment register must be updated first. Until then G0
refuses, and G9 proves absence on the output.

*** COMMERCIAL. ***

CONNECT_MODE is "none". It is the one switch any future qualified-lead,
introduction, referral or sales mechanism would have to change, and the
guard refuses every other value: no such mechanism is authorised.

Run: python3 build-ecosauna-preview.py [--stage]
"""

import pathlib
import re
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import preview_image_treatment as pit  # noqa: E402  shared v1.1 safeguards

HERE = pathlib.Path(__file__).resolve().parent
SITE = HERE.parent
TEMPLATE = HERE / "template-provider-led.html"

STAGE = "--stage" in sys.argv
OUT = (pathlib.Path("/tmp/plotnua-stage/ecosauna-preview.html")
       if STAGE else SITE / "ecosauna-preview.html")

SUPPLIER = "EcoSauna"
EVIDENCE_DATE = "18 October 2026"
SUPPLIER_SITE = "https://www.ecosauna.ie/"
PRODUCTS_URL = SUPPLIER_SITE + "?view=PRODUCTS"
WIZARD_URL = SUPPLIER_SITE + "?view=WIZARD"
DISCOVERY_URL = "https://plotnua.ie/discovery-garden-retreat.html"
PLOTNUA_URL = "https://plotnua.ie/"
CREDIT = "© EcoSauna"
TBC_TEXT = "To be confirmed by EcoSauna"
ILLUS_CAPTION = "Illustration &middot; a generic form, not an EcoSauna product"

# IMAGERY STATE C. Empty by governance. See G0.
ECO_IMAGES = []
# COMMERCIAL. See G10b. The only permitted value today.
CONNECT_MODE = "none"

# ── THE EVIDENCE RECORD ─────────────────────────────────────────────────────
EXPECTED_PRODUCTS = ("Barrel Sauna", "Cube Sauna", "Hot Tub", "Plunge Pool",
                     "Phytosauna")
EXPECTED_NO_INSTALL_OPTION = ("Hot Tub", "Plunge Pool", "Phytosauna")
EXPECTED_FROM = {"Barrel Sauna": 3300, "Cube Sauna": 3200, "Hot Tub": 2300,
                 "Plunge Pool": 1100, "Phytosauna": 2100}

# ── THE RANGE ───────────────────────────────────────────────────────────────
# Every value is from the configurator catalogue or its option price table.
# "line" is the homeowner-facing one-liner: it restates the supplier's own
# description of the product and claims nothing beyond it.
RANGE = [
    {"name": "Barrel Sauna", "key": "barrel", "kind": "Heat",
     "line": "The classic cylindrical garden sauna, in six sizes.",
     "from_eur": 3300,
     "chips": ["4 to 8+ people", "Firewood or electric stove",
               "Spruce or Thermowood"],
     "spec": ["Six sizes, from 2m &times; 1.6m (4 people) to 2m &times; 3.5m "
              "(8+ people)",
              "Spruce as standard; Thermowood by length",
              "Firewood or electric stove; a custom stove is discussed on a "
              "call",
              "Four roof colours and a range of exterior finishes"],
     "extras": ["Larger sizes +&euro;150 to +&euro;1,850",
                "Thermowood +&euro;450 to +&euro;650",
                "Half or full panoramic window +&euro;450 / +&euro;850",
                "Lighting +&euro;400 &middot; porch +&euro;400 &middot; "
                "changing room +&euro;500",
                "Trailer &euro;3,800 or &euro;4,000"],
     "install": "&euro;600&ndash;&euro;800 by size"},
    {"name": "Cube Sauna", "key": "cube", "kind": "Heat",
     "line": "A square sauna with more headroom, in seven sizes.",
     "from_eur": 3200,
     "chips": ["Seven sizes", "Firewood or electric stove",
               "Spruce or Thermowood"],
     "spec": ["Seven sizes, from 1.4m &times; 1.6m &times; 2m high to "
              "2m &times; 3.5m",
              "The two smallest sizes are listed with an electric stove",
              "Spruce as standard; Thermowood by size",
              "Glass wall, porch and changing room among the extras"],
     "extras": ["Larger sizes +&euro;200 to +&euro;2,550",
                "Thermowood +&euro;350 to +&euro;650",
                "Glass wall +&euro;800 &middot; full panoramic window "
                "+&euro;850",
                "Porch +&euro;400 &middot; changing room +&euro;600"],
     "install": "&euro;650&ndash;&euro;850 by size"},
    {"name": "Hot Tub", "key": "tub", "kind": "Soak",
     "line": "A wood-fired or electric hot tub, from two people to eight or "
             "more.",
     "from_eur": 2300,
     "chips": ["Five sizes", "Inside or outside stove", "2 to 8+ people"],
     "spec": ["Five sizes, from 1m &times; 2m for two people to 2.25m "
              "diameter for 8+",
              "Inside or outside stove, by size",
              "Seven inside colours and a range of exterior finishes"],
     "extras": ["Larger sizes +&euro;600 to +&euro;1,050",
                "Insulated cover +&euro;300 &middot; air jets +&euro;300",
                "Extra spa jets +&euro;50 &middot; stove for salt water "
                "+&euro;250"],
     "install": None},
    {"name": "Plunge Pool", "key": "plunge", "kind": "Cold",
     "line": "A compact cold plunge for the garden, 1.05m across.",
     "from_eur": 1100,
     "chips": ["1.05m &times; 1.10m high", "Fibreglass inside",
               "Lid and stair listed"],
     "spec": ["1.05m diameter &times; 1.10m high",
              "Listed with a lid, stair, drainage system, timber outside and "
              "fibreglass inside",
              "Three fibreglass colours and a range of exterior finishes"],
     "extras": ["No priced extras are listed in the configurator"],
     "install": None},
    {"name": "Phytosauna", "key": "phyto", "kind": "Steam",
     "line": "A herbal steam cabin you sit in, 130cm tall.",
     "from_eur": 2100,
     "chips": ["130 &times; 78 &times; 78cm", "65kg", "Thermo Aspen"],
     "spec": ["130cm &times; 78cm &times; 78cm, 65kg",
              "Knot-free Thermo Aspen",
              "Listed with a 3-level seat, armrest, footrest, steam supply, "
              "drain and wooden cup"],
     "extras": ["No priced extras are listed in the configurator"],
     "install": None},
]


def eur(n):
    return "&euro;{:,}".format(n)


# ── ORIGINAL GENERIC LINE ILLUSTRATIONS ─────────────────────────────────────
# Drawn here, by hand, as SVG paths. Deliberately schematic: no proportions,
# timber counts, door positions or stove details taken from any EcoSauna
# product. They exist so the image-free state reads as designed, and are
# replaced by authorised photography only through G0.
def _svg(body, vb="0 0 120 80", cls="ev-ico"):
    return ('<svg class="%s" viewBox="%s" fill="none" stroke="currentColor" '
            'stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" '
            'aria-hidden="true" focusable="false" %s>%s</svg>'
            % (cls, vb, pit.ILLUSTRATION_ATTR, body))


ICONS = {
    "barrel": _svg('<path d="M10 66h100"/><ellipse cx="28" cy="40" rx="12" ry="22"/>'
                   '<path d="M28 18h62M28 62h62"/><path d="M90 18a12 22 0 0 1 0 44"/>'
                   '<path d="M46 19v42M64 19v42" opacity=".45"/>'
                   '<path d="M22 46v-12a6 6 0 0 1 12 0v12" class="ev-acc"/>'),
    "cube": _svg('<path d="M10 66h100"/><path d="M26 64V22h68v42"/>'
                 '<path d="M22 22h76" /><path d="M34 64V34h16v30"/>'
                 '<rect x="60" y="32" width="24" height="16" rx="1" class="ev-acc"/>'
                 '<path d="M84 22V12h6v10" opacity=".55"/>'),
    "tub": _svg('<path d="M10 66h100"/><path d="M22 40h66v24H22z"/>'
                '<ellipse cx="55" cy="40" rx="33" ry="6"/>'
                '<path d="M40 34c2-6-2-10 0-16M55 34c2-6-2-10 0-16M70 34c2-6-2-10 0-16" class="ev-acc"/>'
                '<path d="M94 64V30h8v34M98 30V18" opacity=".55"/>'),
    "plunge": _svg('<path d="M10 66h100"/><path d="M44 30h34v34H44z"/>'
                   '<ellipse cx="61" cy="30" rx="17" ry="4"/>'
                   '<path d="M50 40h22" class="ev-acc"/>'
                   '<path d="M30 64V46M30 52h14M30 58h14M38 64V46" opacity=".55"/>'),
    "phyto": _svg('<path d="M10 66h100"/><path d="M44 64V24h32v40"/>'
                  '<path d="M40 24c4-8 36-8 40 0"/><circle cx="60" cy="14" r="5" class="ev-acc"/>'
                  '<path d="M50 40h20M50 50h20" opacity=".5"/>'),
}

HERO_SCENE = _svg(
    # An elevation of an ordinary back garden, in line only. Left: the back of
    # a house. Then a cube cabin, a barrel, a hot tub with steam and a plunge
    # pool, against a boundary fence and a tree. Generic forms, no supplier
    # proportions.
    '<path d="M16 336h568"/>'
    '<path d="M16 336V120l70-46 70 46v216" opacity=".5"/>'
    '<path d="M40 336v-62h36v62M100 200h34v40h-34z" opacity=".5"/>'
    '<path d="M156 300h428" opacity=".22"/>'
    '<path d="M156 264h428" opacity=".22"/>'
    '<path d="M196 264v72M256 264v72M316 264v72M376 264v72M436 264v72M496 264v72M556 264v72" opacity=".16"/>'
    # tree
    '<path d="M556 300V214" opacity=".7"/>'
    '<path d="M556 230c-40-4-56-42-32-68 4-32 50-38 60-9 18 4 16 60-6 70-8 4-14 7-22 7z" opacity=".7"/>'
    # cube cabin
    '<path d="M170 336V230h92v106"/><path d="M164 230h104"/>'
    '<path d="M182 336v-76h26v76"/>'
    '<rect x="220" y="252" width="32" height="24" class="ev-acc"/>'
    '<path d="M248 230v-18h8v18" opacity=".6"/>'
    # barrel
    '<ellipse cx="300" cy="294" rx="18" ry="34"/><path d="M300 260h86M300 328h86"/>'
    '<path d="M386 260a18 34 0 0 1 0 68"/><path d="M328 261v66M356 261v66" opacity=".4"/>'
    '<path d="M292 306v-18a8 8 0 0 1 16 0v18" class="ev-acc"/>'
    '<path d="M370 260v-20h7v20" opacity=".6"/>'
    # hot tub
    '<path d="M410 306h80v30h-80z"/><ellipse cx="450" cy="306" rx="40" ry="7"/>'
    '<path d="M430 296c3-8-3-13 0-21M450 296c3-8-3-13 0-21M470 296c3-8-3-13 0-21" class="ev-acc"/>'
    '<path d="M498 336v-44h9v44M502 292v-14" opacity=".6"/>'
    # plunge
    '<path d="M520 314h40v22h-40z"/><ellipse cx="540" cy="314" rx="20" ry="4"/>'
    '<path d="M528 324h24" class="ev-acc"/>',
    vb="0 0 600 352", cls="ev-scene")


# ── THE OPEN QUESTIONS ─────────────────────────────────────────────────────
QUESTIONS = [
    ("Prices and VAT",
     "Your configurator starts the Barrel Sauna at &euro;3,300, the Hot Tub at "
     "&euro;2,300 and the Plunge Pool at &euro;1,100. Some of your Ireland "
     "pages give &euro;2,800, &euro;3,100 and &euro;1,950. Which should a "
     "homeowner see, and do your prices include VAT?"),
    ("Delivery and timing",
     "Your configurator prices delivery by location and confirms it on "
     "contact, and your county pages say a custom order usually arrives "
     "within 4 to 6 weeks. Is there a typical delivery range we could show, "
     "and does that timescale hold across the range?"),
    ("Installation and cover",
     "Installation is a priced option on the Barrel and Cube Saunas. Is it "
     "also offered for the Hot Tub, Plunge Pool and Phytosauna? And what "
     "would you like a homeowner to know about the warranty on each?"),
]

JOURNEY = [
    ("Discover", "What a garden like theirs could become."),
    ("Check", "What it needs: space, a level base, power."),
    ("Explore", "Real products, in detail."),
    ("Compare", "Options side by side, prices in context."),
    ("Decide", "An informed choice, made in their own time."),
    ("Connect", "When ready, the right supplier."),
]
# EcoSauna appears from Explore onwards.
JOURNEY_SUPPLIER_FROM = "Explore"

WHY = [
    ("Your configurator, understood first",
     "A homeowner sees the starting price and what adds to it &mdash; size, "
     "Thermowood, extras, installation &mdash; before they open your "
     "configurator."),
    ("The base before delivery day",
     "Your own base guidance sits next to the price, so the pad or deck is "
     "planned for, not discovered when the trailer is booked."),
    ("Reached through garden wellness",
     "They arrive having decided they want a sauna, a hot tub or a cold "
     "plunge in their garden, not having typed your name into a search box."),
]

# ── THE DEMONSTRATION COPY (the real Results card) ──────────────────────────
FILL = {
    "SUPPLIER_NAME": SUPPLIER,
    "SUPPLIER_SHORT": SUPPLIER,
    "OFFER_NAME": "Barrel Sauna",
    "VERIFIED_PRICE": "From &euro;3,300",
    "VERIFIED_PRICE_BASIS": "The starting figure EcoSauna&rsquo;s online "
                            "configurator shows for the 2m &times; 1.6m "
                            "spruce Barrel Sauna. Larger sizes, Thermowood, "
                            "extras and installation are priced on top; "
                            "EcoSauna say the configured total is an "
                            "estimate, with the final price and delivery "
                            "confirmed on contact. EcoSauna say they deliver "
                            "to all 32 counties.",
    "VERIFIED_FACT_1_LABEL": "Capacity",
    "VERIFIED_FACT_1_VALUE": "4 people in the 2m &times; 1.6m; 8+ in the "
                             "2m &times; 3.5m",
    "VERIFIED_FACT_2_LABEL": "Sizes",
    "VERIFIED_FACT_2_VALUE": "Six, from 2m &times; 1.6m to 2m &times; 3.5m",
    "VERIFIED_FACT_3": "Firewood or electric stove",
    "VERIFIED_FACT_4": "Spruce as standard; Thermowood from +&euro;450",
    "VERIFIED_FACT_5": "Installation option from &euro;600",
    "THINGS_TO_CHECK": "the figure is the starting configuration, not a "
                       "quote, and delivery is priced by location. "
                       "EcoSauna&rsquo;s own guidance is that the base is "
                       "ready before they arrive: a level concrete pad of at "
                       "least 100mm, a heavy-duty timber deck, or compacted "
                       "gravel with paving flags. An electric stove needs a "
                       "certified electrician to run the supply. And a point "
                       "of ours rather than yours: the local authority is the "
                       "only body that can confirm what a particular site "
                       "requires.",
    "HOMEOWNER_LOCALITY": "Co. Meath",
    "PERSONALISATION": "Shown for a homeowner in Co. Meath, from the location "
                       "they gave us. We don&rsquo;t ask about the base, the "
                       "access or where the power runs, so we wouldn&rsquo;t "
                       "pretend to know.",
}

# ── CLAIMS THE EVIDENCE DOES NOT SUPPORT, OR THAT ARE MARKETING ────────────
BANNED_CLAIM_PHRASES = [
    "premier", "the leading", "leading provider", "number one", "best price",
    "cheapest", "top-tier", "pinnacle", "luxury",
    "manufactured in ireland", "made in ireland", "irish made", "irish-made",
    "irish built", "irish-built", "handcrafted in", "we manufacture",
    "built in ireland", "estonia",
    "warranty of", "year warranty", "comprehensive warranty",
    "guaranteed for", "we guarantee", "lead time of", "free delivery",
    "delivery included", "inc. vat", "including vat", "incl. vat",
    "ex vat", "excluding vat", "in stock", "available now",
    "planning exempt", "exempted development", "no planning permission",
    "does not need planning", "don't need planning",
    "inflammation", "immune", "cures", "treats", "detox", "healing",
    "cardiovascular", "respiratory", "health benefit",
    "highly recommended", "stellar customer service", "blown away",
    "installations in the", "completed over", "loved by",
    "harvia",
]


def die(msg):
    """A builder that crashes has not refused; it has merely failed."""
    print("REFUSED: " + msg)
    sys.exit(1)


def live_grant_or_die():
    """G0 READS THE REGISTER, NOT A COMMENT. Delegates to the shared v1.1 T1
    gate (preview_image_treatment.live_grant): imagery needs a LIVE grant for
    ecosauna.ie carrying the exact credit this page prints."""
    try:
        row = pit.live_grant(SITE, "ecosauna.ie", CREDIT)
    except ValueError as e:
        die(str(e))
    if row is None:
        die("EcoSauna imagery was added, but there is no LIVE grant for "
            "ecosauna.ie in image-rights-manifest.json. The reply asked to see "
            "a private preview, which is not a grant. UNKNOWN is not GRANTED.")
    return row


# ── PAGE PARTS ──────────────────────────────────────────────────────────────
def product_card(m):
    chips = "".join('<li>%s</li>' % c for c in m["chips"])
    spec = "".join('<li>%s</li>' % s for s in m["spec"])
    extras = "".join('<li>%s</li>' % s for s in m["extras"])
    if m["install"] is None:
        inst = '<span class="ev-tbc">%s</span>' % TBC_TEXT
    else:
        inst = m["install"]
    return """      <article class="ev-card" id="p-%(key)s" aria-labelledby="p-%(key)s-h">
        <div class="ev-card-art">%(icon)s<span class="ev-kind">%(kind)s</span></div>
        <div class="ev-card-body">
          <h3 id="p-%(key)s-h">%(name)s</h3>
          <p class="ev-line">%(line)s</p>
          <p class="ev-price"><span class="ev-from">From</span> %(price)s</p>
          <p class="ev-basis">Configurator starting price &middot; not a quote</p>
          <ul class="ev-chips">%(chips)s</ul>
          <dl class="ev-install"><dt>Installation option</dt><dd>%(inst)s</dd></dl>
          <details class="ev-more">
            <summary><span>Specification &amp; costs on top</span><i aria-hidden="true"></i></summary>
            <div class="ev-more-in">
              <h4>Published specification</h4>
              <ul>%(spec)s</ul>
              <h4>Priced on top</h4>
              <ul>%(extras)s</ul>
              <h4>Still to confirm</h4>
              <ul><li>Whether the price includes VAT</li><li>The delivery charge for the homeowner&rsquo;s area</li><li>What a homeowner should know about the warranty</li></ul>
            </div>
          </details>
        </div>
      </article>""" % dict(key=m["key"], icon=ICONS[m["key"]], kind=m["kind"],
                            name=m["name"], line=m["line"],
                            price=eur(m["from_eur"]), chips=chips, inst=inst,
                            spec=spec, extras=extras)


def glance():
    top = max(m["from_eur"] for m in RANGE)
    rows = []
    for m in sorted(RANGE, key=lambda m: m["from_eur"]):
        pct = round(100.0 * m["from_eur"] / top, 1)
        rows.append('<li><a href="#p-%s">%s</a><span class="ev-bar">'
                    '<span style="width:%s%%"></span></span><b>%s</b></li>'
                    % (m["key"], m["name"], pct, eur(m["from_eur"])))
    return ('<div class="ev-glance" aria-label="Starting prices at a glance">'
            '<p class="ev-eyebrow">Starting prices at a glance</p>'
            '<ul>%s</ul><p class="ev-glance-note">Configurator starting '
            'figures. Size, timber, extras, installation and delivery are on '
            'top; VAT is not stated.</p></div>' % "".join(rows))


def journey():
    out = []
    on = False
    for i, (step, text) in enumerate(JOURNEY, 1):
        if step == JOURNEY_SUPPLIER_FROM:
            on = True
        out.append('<li class="ev-step%s"%s><span class="ev-step-n">%02d</span>'
                   '<b>%s</b><span class="ev-step-t">%s</span></li>'
                   % (" is-supplier" if on else "",
                      ' data-connect-mode="%s"' % CONNECT_MODE
                      if step == "Connect" else "", i, step, text))
    return "\n".join(out)


def build_body(stage):
    cards = "\n".join(product_card(m) for m in RANGE)
    qs = "\n".join('<div class="ev-q"><span class="ev-q-n">%02d</span>'
                   '<h3>%s</h3><p>%s</p></div>' % (i, h, t)
                   for i, (h, t) in enumerate(QUESTIONS, 1))
    why = "\n".join('<div class="ev-why-c"><span class="ev-why-n">%02d</span>'
                    '<h3>%s</h3><p>%s</p></div>' % (i, h, t)
                    for i, (h, t) in enumerate(WHY, 1))
    return """<a class="ev-skip" href="#main">Skip to the preview</a>
<aside class="ev-bar-top" aria-label="Preview status"><div class="ev-wrap">
  <span><strong>Private supplier preview</strong> &middot; Prepared for %(sup)s</span>
  <span class="ev-bar-meta">Unlisted &middot; not published &middot; %(date)s</span>
</div></aside>

<header class="ev-hero">
  <div class="ev-wrap">
    <a class="ev-wordmark" href="%(plotnua)s" rel="noopener">PlotNua</a>
    <div class="ev-hero-grid">
      <div class="ev-hero-copy">
        <p class="ev-eyebrow ev-on-dark">A PlotNua Discovery &middot; Garden Retreat</p>
        <h1>Your garden.<br>A different kind of escape.</h1>
        <p class="ev-sub">From an ordinary outdoor space to a private wellness retreat.</p>
        <p class="ev-intro">This is how EcoSauna could appear to Irish homeowners exploring garden saunas, hot tubs and cold plunges on PlotNua.</p>
        <div class="ev-actions">
          <a class="ev-btn ev-btn-light" href="#products">See the five products</a>
          <a class="ev-btn ev-btn-line" href="%(site)s" rel="noopener">Visit ecosauna.ie <span aria-hidden="true">&#8599;</span></a>
        </div>
      </div>
      <figure class="ev-hero-art">
        %(scene)s
        <figcaption>Illustration &middot; generic forms, not EcoSauna products</figcaption>
      </figure>
    </div>
  </div>
</header>

<main id="main">

<section class="ev-sec ev-journey-sec" aria-labelledby="j-h">
  <div class="ev-wrap">
    <p class="ev-eyebrow"><span class="ev-num">01</span> The homeowner journey</p>
    <h2 id="j-h">They arrive with the thinking already done.</h2>
    <p class="ev-lede">Homeowners start in <a href="%(disc)s" rel="noopener"><i>Garden Retreat</i></a>, our Discovery on garden saunas, hot tubs and cold plunges in Ireland. EcoSauna appears once they are looking at real products.</p>
    <ol class="ev-journey">
%(journey)s
    </ol>
    <p class="ev-journey-key"><span aria-hidden="true"></span>Where EcoSauna appears</p>
  </div>
</section>

<section class="ev-sec ev-demo-sec" aria-labelledby="d-h">
  <div class="ev-wrap">
    <div class="ev-demo-head">
      <div>
        <p class="ev-eyebrow"><span class="ev-num">02</span> On PlotNua</p>
        <h2 id="d-h">This is where EcoSauna would appear.</h2>
      </div>
      <span class="illus-tag">Illustrative preview</span>
    </div>
    <p class="ev-lede">The real PlotNua results screen, filled only with what your own website publishes.</p>
%(stage)s
  </div>
</section>

<section class="ev-sec ev-range-sec" id="products" aria-labelledby="r-h">
  <div class="ev-wrap">
    <p class="ev-eyebrow"><span class="ev-num">03</span> The range</p>
    <div class="ev-range-head">
      <h2 id="r-h">Five ways to bring it home.</h2>
      <p class="ev-lede">Sizes and starting prices from <a href="%(wizard)s" rel="noopener">your online configurator</a>. Please check each one.</p>
    </div>
    %(glance)s
    <p class="ev-swipe" aria-hidden="true">Swipe through all five</p>
    <div class="ev-cards">
%(cards)s
    </div>
    <p class="ev-range-note">Your configurator says its total is an estimate: the final price and the delivery charge, which depends on location, are confirmed when you&rsquo;re contacted.</p>
  </div>
</section>

<section class="ev-sec ev-dark" aria-labelledby="q-h">
  <div class="ev-wrap">
    <p class="ev-eyebrow ev-on-dark"><span class="ev-num">04</span> Before anything goes live</p>
    <h2 id="q-h">Three things we&rsquo;d like to check with you.</h2>
    <div class="ev-qs">
%(qs)s
    </div>
  </div>
</section>

<section class="ev-sec" aria-labelledby="w-h">
  <div class="ev-wrap">
    <p class="ev-eyebrow"><span class="ev-num">05</span> Why this could be useful</p>
    <h2 id="w-h">What PlotNua adds before they reach you.</h2>
    <div class="ev-why">
%(why)s
    </div>
  </div>
</section>

<section class="ev-sec ev-close" aria-labelledby="c-h">
  <div class="ev-wrap ev-close-in">
    <h2 id="c-h">Does this represent EcoSauna accurately for an Irish homeowner?</h2>
    <p>If anything here is wrong, out of date or missing &mdash; a price, a size, what installation covers &mdash; tell us and we&rsquo;ll correct it before anything is published.</p>
    <a class="ev-btn ev-btn-dark" href="%(site)s" rel="noopener">EcoSauna&rsquo;s website <span aria-hidden="true">&#8599;</span></a>
  </div>
</section>

</main>

<footer class="ev-foot">
  <div class="ev-wrap">
    <p class="credit-line">Every figure on this page is published by %(sup)s and was read from <a href="%(prod)s" rel="noopener">your products</a>, <a href="%(wizard)s" rel="noopener">your online configurator</a> and <a href="%(site)s" rel="noopener">ecosauna.ie</a> on %(date)s. No %(sup)s photography is used anywhere on this page; the drawings are generic illustrations. %(credit)s</p>
    <p class="ev-foot-line"><span class="ev-foot-mark">PlotNua</span> Private preview prepared for %(sup)s &middot; %(date)s</p>
  </div>
</footer>
""" % dict(sup=SUPPLIER, date=EVIDENCE_DATE, plotnua=PLOTNUA_URL,
           site=SUPPLIER_SITE, prod=PRODUCTS_URL, wizard=WIZARD_URL,
           disc=DISCOVERY_URL, scene=HERO_SCENE, journey=journey(),
           stage=stage, glance=glance(), cards=cards, qs=qs, why=why,
           credit=CREDIT)


EV_CSS = r"""<style>
/* ══ ECOSAUNA v2 SHELL — PlotNua premium supplier-preview language ═════════
   Scoped under body.ev. Tokens follow the approved editorial homepage and
   A Home for Art: forest, ivory, paper, terracotta; Fraunces + Work Sans. */
body.ev{
  --ev-forest:#1F3B2E; --ev-forest-2:#2B4A3C; --ev-ivory:#F2EFE6;
  --ev-paper:#F8F5EC; --ev-sheet:#FCFBF7; --ev-terra:#BD6A46; --ev-terra-t:#A4532F;
  --ev-sage:#8FAF8A; --ev-soft:#55605A; --ev-ink:#1F3B2E;
  --ev-hair:rgba(31,59,46,.14); --ev-on-dark:rgba(242,239,230,.82);
  --ev-wrap:1200px; --ev-gut:clamp(20px,4vw,40px);
  background:var(--ev-paper); color:var(--ev-soft);
  font-family:'Work Sans',system-ui,sans-serif; font-size:16px; line-height:1.6;
}
body.ev .ev-wrap{ max-width:var(--ev-wrap); margin:0 auto; padding:0 var(--ev-gut); }
body.ev h1, body.ev h2, body.ev h3{ font-family:'Fraunces',Georgia,serif; color:var(--ev-ink);
  letter-spacing:-.015em; margin:0; max-width:none; }
body.ev a{ color:inherit; }
body.ev p{ max-width:62ch; }
.ev-skip{ position:absolute; left:-9999px; }
.ev-skip:focus{ left:16px; top:12px; z-index:50; background:#fff; padding:10px 14px; }

.ev-eyebrow{ font-size:11px; font-weight:600; letter-spacing:.22em; text-transform:uppercase;
  color:var(--ev-soft); margin:0 0 18px; display:flex; align-items:center; gap:12px; }
.ev-eyebrow.ev-on-dark{ color:var(--ev-on-dark); }
.ev-num{ font-family:'Fraunces',serif; font-weight:300; font-size:20px; letter-spacing:0;
  color:var(--ev-terra-t); }
.ev-on-dark .ev-num{ color:#E3A383; }
.ev-lede{ font-size:clamp(16px,1.3vw,18px); line-height:1.6; color:var(--ev-soft); margin:18px 0 0; }
.ev-lede a{ text-underline-offset:3px; text-decoration-color:var(--ev-terra); }

/* private bar */
.ev-bar-top{ background:#16291F; color:var(--ev-ivory); font-size:13px; padding:10px 0; }
.ev-bar-top .ev-wrap{ display:flex; justify-content:space-between; gap:8px 24px; flex-wrap:wrap; }
.ev-bar-top strong{ font-weight:600; letter-spacing:.18em; text-transform:uppercase; font-size:11px; }
.ev-bar-meta{ color:rgba(242,239,230,.75); }

/* hero */
.ev-hero{ background:var(--ev-forest); color:var(--ev-ivory); padding:28px 0 clamp(56px,7vw,96px); overflow:hidden; }
.ev-wordmark{ font-family:'Fraunces',serif; font-weight:500; letter-spacing:.28em; text-transform:uppercase;
  font-size:15px; text-decoration:none; color:var(--ev-ivory)!important; display:inline-block;
  padding:10px 0; min-height:44px; }
.ev-hero-grid{ display:grid; grid-template-columns:1.05fr 1fr; gap:clamp(32px,5vw,72px);
  align-items:center; margin-top:clamp(28px,5vw,64px); }
body.ev .ev-hero h1{ color:var(--ev-ivory); font-weight:600; font-size:clamp(44px,6.2vw,86px);
  line-height:.98; letter-spacing:-.02em; }
.ev-sub{ font-family:'Fraunces',serif; font-style:italic; font-size:clamp(20px,2vw,26px);
  line-height:1.35; color:var(--ev-ivory); margin:26px 0 0; }
.ev-intro{ color:var(--ev-on-dark); font-size:16px; margin:18px 0 0; max-width:46ch; }
.ev-actions{ display:flex; flex-wrap:wrap; gap:12px; margin-top:34px; }
.ev-btn{ display:inline-flex; align-items:center; gap:8px; min-height:48px; padding:0 22px;
  font-size:12.5px; font-weight:600; letter-spacing:.14em; text-transform:uppercase;
  text-decoration:none; border-radius:2px; transition:transform .2s ease, background .2s ease; }
.ev-btn:hover{ transform:translateY(-1px); }
.ev-btn:focus-visible{ outline:2px solid var(--ev-terra); outline-offset:3px; }
.ev-btn-light{ background:var(--ev-ivory); color:var(--ev-forest)!important; box-shadow:inset 0 -2px 0 var(--ev-terra); }
.ev-btn-line{ border:1px solid rgba(242,239,230,.55); color:var(--ev-ivory)!important; }
.ev-btn-line:hover{ background:rgba(242,239,230,.08); }
.ev-btn-dark{ background:var(--ev-forest); color:var(--ev-ivory)!important; }
.ev-hero-art{ margin:0; position:relative; border:1px solid rgba(242,239,230,.18);
  background:rgba(242,239,230,.03); padding:clamp(18px,2.4vw,32px) clamp(18px,2.4vw,32px) 16px; }
.ev-scene{ display:block; width:100%; height:auto; color:rgba(242,239,230,.9); }
.ev-scene *, .ev-ico *{ vector-effect:non-scaling-stroke; stroke-width:1.5px; }
.ev-scene .ev-acc, .ev-ico .ev-acc{ color:var(--ev-terra); stroke:var(--ev-terra); }
.ev-hero-art figcaption{ font-size:10.5px; font-weight:600; letter-spacing:.18em; text-transform:uppercase;
  color:rgba(242,239,230,.72); margin-top:10px; }

/* sections */
.ev-sec{ padding:clamp(72px,9vw,128px) 0 0; }
body.ev .ev-sec h2{ font-size:clamp(32px,4vw,52px); line-height:1.04; font-weight:500; max-width:20ch; }

/* journey */
.ev-journey{ list-style:none; margin:48px 0 0; padding:0; display:grid;
  grid-template-columns:repeat(6,1fr); position:relative; counter-reset:none; }
.ev-journey::before{ content:""; position:absolute; left:0; right:0; top:22px; height:1px; background:var(--ev-hair); }
.ev-step{ position:relative; padding:0 18px 0 0; }
.ev-step-n{ position:relative; z-index:1; display:inline-flex; align-items:center; justify-content:center;
  width:44px; height:44px; border-radius:50%; background:var(--ev-paper); border:1px solid var(--ev-hair);
  font-family:'Fraunces',serif; font-size:15px; color:var(--ev-ink); }
.ev-step.is-supplier .ev-step-n{ background:var(--ev-forest); border-color:var(--ev-forest); color:var(--ev-ivory); }
.ev-step.is-supplier::after{ content:""; position:absolute; left:0; right:0; top:22px; height:2px; background:var(--ev-terra); z-index:0; }
.ev-step:last-child.is-supplier::after{ right:auto; width:22px; }
.ev-step b{ display:block; font-family:'Fraunces',serif; font-weight:500; font-size:21px; color:var(--ev-ink); margin:18px 0 6px; }
.ev-step-t{ display:block; font-size:14px; line-height:1.45; color:var(--ev-soft); }
.ev-journey-key{ display:flex; align-items:center; gap:10px; font-size:12px; letter-spacing:.14em;
  text-transform:uppercase; color:var(--ev-soft); margin:28px 0 0; }
.ev-journey-key span{ width:28px; height:2px; background:var(--ev-terra); display:inline-block; }

/* demonstration */
.ev-demo-head{ display:flex; justify-content:space-between; align-items:flex-end; gap:20px; flex-wrap:wrap; }
body.ev .illus-tag{ color:var(--ev-soft); border-color:var(--ev-hair); }
body.ev .screen{ margin-top:32px; border-radius:10px; border-color:var(--ev-hair);
  box-shadow:0 30px 80px -40px rgba(31,59,46,.45), 0 2px 6px rgba(31,59,46,.05); }
body.ev .screen-chrome{ background:var(--ev-ivory); }
body.ev .screen-url{ color:#585D55; }
body.ev .pn-photo-slot{ background:linear-gradient(160deg,#21402F 0%,#1B3527 100%);
  box-shadow:none; color:rgba(242,239,230,.88); gap:16px; padding:28px; }
body.ev .pn-photo-slot .ev-ico{ width:min(78%,420px); height:auto; color:rgba(242,239,230,.88); }
body.ev .pn-photo-slot b{ color:rgba(242,239,230,.8); font-size:10.5px; }
/* PARITY, NOT A RESTYLE (18 Oct 2026). Production Results draws this note in
   --pn-body (your-plot.html, #screen-match-results .results-hero-budget-note);
   the template's UI kit had drifted to --oak, which failed contrast (4.29:1).
   Re-pointing it here makes the preview MORE faithful to production. */
body.ev .pn-stage .results-hero-budget-note{ color:var(--pn-body); }
body.ev .hero-secondary .is-illustrative{ color:var(--ev-soft); cursor:default; text-decoration:none; }
body.ev .hero-secondary .is-illustrative small{ font-size:10px; letter-spacing:.14em; text-transform:uppercase; margin-left:6px; }

/* range */
.ev-range-head{ display:grid; grid-template-columns:1fr 1fr; gap:24px 48px; align-items:end; }
.ev-range-head .ev-lede{ margin:0; }
.ev-glance{ margin:48px 0 0; padding:28px 32px; background:var(--ev-sheet); border:1px solid var(--ev-hair); }
.ev-glance ul{ list-style:none; margin:0; padding:0; display:grid; gap:12px; }
.ev-glance li{ display:grid; grid-template-columns:150px 1fr 84px; align-items:center; gap:18px; }
.ev-glance li a{ font-family:'Fraunces',serif; font-size:17px; color:var(--ev-ink); text-decoration:none;
  min-height:32px; display:flex; align-items:center; }
.ev-glance li a:hover{ color:var(--ev-terra-t); }
.ev-glance .ev-bar{ height:6px; background:rgba(31,59,46,.08); border-radius:3px; overflow:hidden; }
.ev-glance .ev-bar span{ display:block; height:100%; background:var(--ev-forest); border-radius:3px; }
.ev-glance li b{ font-family:'Fraunces',serif; font-weight:500; font-size:17px; color:var(--ev-ink); text-align:right; }
.ev-glance-note{ font-size:13.5px; margin:16px 0 0; color:var(--ev-soft); }
.ev-cards{ display:grid; grid-template-columns:repeat(6,1fr); gap:20px; margin-top:20px; align-items:start; }
.ev-card{ grid-column:span 2; background:var(--ev-sheet); border:1px solid var(--ev-hair);
  display:flex; flex-direction:column; transition:box-shadow .25s ease, transform .25s ease; }
.ev-card:nth-child(4), .ev-card:nth-child(5){ grid-column:span 3; }
.ev-card:nth-child(4) .ev-card-art, .ev-card:nth-child(5) .ev-card-art{ aspect-ratio:2.4/1; }
.ev-card:hover{ box-shadow:0 24px 50px -34px rgba(31,59,46,.5); }
.ev-card-art{ position:relative; background:var(--ev-forest); color:rgba(242,239,230,.9);
  aspect-ratio:16/9; display:flex; align-items:center; justify-content:center; padding:18px; }
.ev-card-art .ev-ico{ width:62%; max-width:230px; height:auto; }
.ev-kind{ position:absolute; left:16px; top:14px; font-size:10.5px; font-weight:600; letter-spacing:.2em;
  text-transform:uppercase; color:rgba(242,239,230,.75); }
.ev-card-body{ padding:24px 24px 8px; display:flex; flex-direction:column; flex:1; }
body.ev .ev-card h3{ font-size:26px; font-weight:500; }
.ev-line{ font-size:15px; margin:8px 0 0; color:var(--ev-soft); }
.ev-price{ font-family:'Fraunces',serif; font-size:34px; color:var(--ev-ink); margin:20px 0 0; line-height:1; }
.ev-from{ font-family:'Work Sans',sans-serif; font-size:12px; letter-spacing:.16em; text-transform:uppercase;
  color:var(--ev-soft); margin-right:4px; vertical-align:middle; }
.ev-basis{ font-size:12.5px; color:var(--ev-soft); margin:8px 0 0; }
.ev-chips{ list-style:none; margin:18px 0 0; padding:0; display:flex; flex-wrap:wrap; gap:8px; }
.ev-chips li{ font-size:12.5px; line-height:1; padding:8px 11px; border:1px solid var(--ev-hair); border-radius:999px; color:var(--ev-ink); }
.ev-install{ margin:18px 0 0; padding:14px 0 0; border-top:1px solid var(--ev-hair); display:flex;
  justify-content:space-between; gap:12px; font-size:14px; }
.ev-install dt{ color:var(--ev-soft); }
.ev-install dd{ margin:0; color:var(--ev-ink); font-weight:500; text-align:right; }
.ev-tbc{ font-style:italic; font-weight:400; color:var(--ev-terra-t); }
.ev-more{ margin-top:auto; border-top:1px solid var(--ev-hair); }
.ev-card .ev-install + .ev-more{ margin-top:14px; }
.ev-more summary{ list-style:none; cursor:pointer; display:flex; justify-content:space-between; align-items:center;
  min-height:52px; gap:16px; font-size:12.5px; font-weight:600; letter-spacing:.12em; text-transform:uppercase; color:var(--ev-ink); }
.ev-more summary::-webkit-details-marker{ display:none; }
.ev-more summary:focus-visible{ outline:2px solid var(--ev-terra); outline-offset:2px; }
.ev-more summary i{ position:relative; width:14px; height:14px; }
.ev-more summary i::before, .ev-more summary i::after{ content:""; position:absolute; left:0; right:0; top:6px;
  height:1.5px; background:var(--ev-terra); transition:transform .25s ease; }
.ev-more summary i::after{ transform:rotate(90deg); }
.ev-more[open] summary i::after{ transform:rotate(0deg); }
.ev-more-in{ padding:0 0 18px; }
.ev-more h4{ font-size:11px; font-weight:600; letter-spacing:.18em; text-transform:uppercase; color:var(--ev-soft); margin:14px 0 8px; }
.ev-more ul{ margin:0; padding:0 0 0 16px; font-size:14px; line-height:1.5; color:var(--ev-ink); }
.ev-more li{ margin:0 0 4px; }
.ev-range-note{ font-size:14px; margin:28px 0 0; }
.ev-swipe{ display:none; align-items:center; gap:10px; margin:22px 0 0; font-size:11px; font-weight:600;
  letter-spacing:.18em; text-transform:uppercase; color:var(--ev-soft); }
.ev-swipe::after{ content:"\2192"; color:var(--ev-terra); font-size:14px; }

/* dark questions */
.ev-dark{ background:var(--ev-forest); color:var(--ev-ivory); margin-top:clamp(72px,9vw,128px);
  padding-bottom:clamp(72px,9vw,120px); }
body.ev .ev-dark h2{ color:var(--ev-ivory); }
.ev-qs{ display:grid; grid-template-columns:repeat(3,1fr); gap:20px; margin-top:44px; }
.ev-q{ background:var(--ev-forest-2); border-top:3px solid var(--ev-terra); padding:28px 26px 30px; }
.ev-q-n{ font-family:'Fraunces',serif; font-weight:300; font-size:30px; color:#E3A383; }
body.ev .ev-q h3{ color:var(--ev-ivory); font-size:23px; font-weight:500; margin:10px 0 12px; }
.ev-q p{ color:var(--ev-on-dark); font-size:15px; margin:0; }

/* why */
.ev-why{ display:grid; grid-template-columns:repeat(3,1fr); gap:clamp(24px,3vw,48px); margin-top:44px; }
.ev-why-c{ border-top:1px solid var(--ev-ink); padding-top:20px; }
.ev-why-n{ font-family:'Fraunces',serif; font-weight:300; font-size:44px; color:var(--ev-terra-t); line-height:1; }
body.ev .ev-why-c h3{ font-size:22px; font-weight:500; margin:14px 0 10px; }
.ev-why-c p{ font-size:15px; margin:0; }

/* close */
.ev-close-in{ text-align:center; display:flex; flex-direction:column; align-items:center; }
body.ev .ev-close h2{ max-width:22ch; font-size:clamp(30px,3.6vw,46px); }
.ev-close p{ margin:20px 0 28px; font-size:17px; }

/* footer */
.ev-foot{ margin-top:clamp(72px,9vw,120px); border-top:1px solid var(--ev-hair); padding:28px 0 48px; }
body.ev .credit-line{ background:none; border:0; padding:0; font-size:13px; color:var(--ev-soft); max-width:80ch; }
.ev-foot-line{ font-size:13px; margin:18px 0 0; color:var(--ev-soft); display:flex; gap:14px; align-items:center; flex-wrap:wrap; }
.ev-foot-mark{ font-family:'Fraunces',serif; letter-spacing:.24em; text-transform:uppercase; color:var(--ev-ink); }

@media (max-width:1100px){
  .ev-cards{ grid-template-columns:repeat(2,1fr); }
  .ev-card, .ev-card:nth-child(4), .ev-card:nth-child(5){ grid-column:auto; }
  .ev-card:nth-child(5){ grid-column:1 / -1; }
}
@media (max-width:900px){
  .ev-hero-grid{ grid-template-columns:1fr; }
  .ev-journey{ grid-template-columns:1fr; gap:0; margin-top:36px; }
  .ev-journey::before{ left:22px; right:auto; top:0; bottom:0; width:1px; height:auto; }
  .ev-step{ display:grid; grid-template-columns:44px 1fr; column-gap:18px; padding:0 0 22px; }
  .ev-step-n{ grid-row:1 / span 2; }
  .ev-step b{ margin:2px 0 2px; font-size:20px; }
  .ev-step.is-supplier::after{ left:21px; right:auto; top:0; bottom:0; width:2px; height:auto; }
  .ev-step:last-child.is-supplier::after{ width:2px; height:22px; bottom:auto; }
  .ev-range-head{ grid-template-columns:1fr; }
  .ev-qs, .ev-why{ grid-template-columns:1fr; }
}
@media (max-width:640px){
  body.ev{ font-size:16px; }
  .ev-bar-top{ font-size:12px; }
  body.ev .ev-hero h1{ font-size:clamp(40px,11.5vw,54px); }
  .ev-actions .ev-btn{ flex:1 1 100%; justify-content:center; }
  .ev-hero-art{ padding:14px 14px 10px; }
  .ev-glance{ padding:20px 18px; }
  .ev-glance li{ grid-template-columns:1fr auto; gap:6px 12px; }
  .ev-glance .ev-bar{ grid-column:1 / -1; grid-row:2; }
  .ev-cards{ display:flex; align-items:flex-start; gap:12px; overflow-x:auto; scroll-snap-type:x mandatory;
    margin:20px calc(-1 * var(--ev-gut)) 0; padding:0 var(--ev-gut) 8px;
    scroll-padding:0 var(--ev-gut); -webkit-overflow-scrolling:touch; scrollbar-width:none; }
  .ev-cards::-webkit-scrollbar{ display:none; }
  .ev-card, .ev-card:nth-child(4), .ev-card:nth-child(5){ flex:0 0 86%; scroll-snap-align:start; }
  .ev-card:nth-child(4) .ev-card-art, .ev-card:nth-child(5) .ev-card-art{ aspect-ratio:2.2/1; }
  .ev-swipe{ display:flex!important; }
  .ev-card-art{ aspect-ratio:2.2/1; }
  /* MOBILE CARD RHYTHM (18 Oct 2026 refinement). One shape for all five:
     price and basis read as one group with room around it; installation is
     a stacked label/value pinned above the specification, so every card
     ends on the same line regardless of how many chips it carries. */
  .ev-cards{ align-items:stretch; }
  .ev-card-body{ padding:22px 20px 4px; }
  .ev-line{ margin-top:6px; }
  .ev-price{ font-size:32px; margin-top:24px; }
  .ev-basis{ margin-top:8px; }
  .ev-chips{ margin-top:20px; }
  .ev-install{ margin-top:auto; padding-top:16px; flex-direction:column; gap:3px;
    justify-content:flex-start; }
  .ev-card .ev-chips + .ev-install{ margin-top:auto; }
  .ev-install dt{ font-size:11px; font-weight:600; letter-spacing:.16em; text-transform:uppercase; }
  .ev-install dd{ text-align:left; font-size:15px; }
  .ev-card-body > .ev-chips{ margin-bottom:22px; }
  .ev-card .ev-install + .ev-more{ margin-top:16px; }
  .ev-more summary{ font-size:11.5px; letter-spacing:.1em; }
}
@media (prefers-reduced-motion:reduce){
  body.ev *{ transition:none!important; }
}
</style>
"""


def main():
    src = TEMPLATE.read_text(encoding="utf-8")

    # G0 · IMAGERY REQUIRES A LIVE GRANT IN THE REGISTER. Not used today.
    if ECO_IMAGES:
        live_grant_or_die()
        die("a live grant exists, but this builder's image rendering path is "
            "not yet enabled: remove EcoSauna from preview-only-suppliers.json "
            "and add the rendering deliberately, with its own proof.")

    # G10b · NO COMMERCIAL MECHANISM IS AUTHORISED.
    if CONNECT_MODE != "none":
        die("CONNECT_MODE is %r. No lead, introduction, referral, commission "
            "or sales mechanism is authorised for this preview." % CONNECT_MODE)

    # G1 · HEAD AND STYLESHEET from the template, verbatim (robots, fonts, UI
    # kit). Everything after <body> is rebuilt.
    # Template v2 (27 Oct 2026): the template's body carries the premium
    # design classes; this page replaces the body wholesale, as before.
    head_end = src.find("<body")
    if head_end < 0 or len(re.findall(r"<body[ >]", src)) != 1:
        die("the template's <body> anchor was not found exactly once.")
    head = src[:head_end]

    # G1b · THE DEMONSTRATION, lifted verbatim from the template.
    sm = re.search(r'\n  <div class="screen">\n.*?\n    </div><!-- /pn-stage -->\n  </div>\n(?=</section>)',
                   src, re.S)
    if not sm:
        die("the demonstration screen block was not found. Not guessing.")
    stage = sm.group(0)
    if stage.count('<div class="pn-stage">') != 1:
        die("the demonstration does not carry exactly one .pn-stage.")

    # G1c · THE TWO "#" LINKS, fixed exactly once each.
    old_ask = '<a class="hero-secondary-link" href="#">Ask PlotNua</a>'
    old_exp = ('<a class="hero-secondary-link" href="#">Explore with '
               '{{SUPPLIER_SHORT}} &rarr;</a>')
    if stage.count(old_ask) != 1 or stage.count(old_exp) != 1:
        die("the demonstration's two placeholder links were not found exactly "
            "once each. The template has moved.")
    stage = stage.replace(
        old_ask, '<span class="hero-secondary-link is-illustrative">Ask PlotNua'
                 '<small>Illustrative</small></span>')
    stage = stage.replace(
        old_exp, '<a class="hero-secondary-link" href="%s" rel="noopener">'
                 'Explore with {{SUPPLIER_SHORT}} &rarr;</a>' % SUPPLIER_SITE)
    # G1d · Inert controls are marked inert, never left looking live.
    for cls in ("my-plot-access", "match-card-save-primary is-saved",
                "match-card-open-myplot-link"):
        needle = '<button type="button" class="%s"' % cls
        if stage.count(needle) != 1:
            die("the demonstration control %r was not found exactly once." % cls)
        stage = stage.replace(needle, needle + ' inert tabindex="-1"')

    # G3 · THE IMAGE POSITION: an original generic illustration and exactly
    # one caption saying so. Nothing else.
    old_slot = '<div class="pn-photo-slot"><b>Your image here</b></div>'
    if stage.count(old_slot) != 1:
        die("the photo slot was not found exactly once. The template has moved.")
    expected_slot_inner = ICONS["barrel"] + "<b>%s</b>" % ILLUS_CAPTION
    stage = stage.replace(old_slot, '<div class="pn-photo-slot" role="img" '
                          'aria-label="Generic illustration of a garden sauna">'
                          + expected_slot_inner + '</div>')

    for key, value in FILL.items():
        needle = "{{%s}}" % key
        if needle not in stage and needle not in head:
            die("token %s is not in the template. The template has moved." % needle)
        stage = stage.replace(needle, value)
        head = head.replace(needle, value)

    src = (head.replace("</style>\n</head>", "</style>\n" + EV_CSS + "</head>")
           + '<body class="ev">\n' + build_body(stage) + "</body>\n</html>\n")
    if EV_CSS not in src:
        die("the v2 stylesheet did not reach the head.")

    # G4 · No token left behind.
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

    # G3 (output) · the slot carries exactly the illustration and its caption.
    slot = re.search(r'<div class="pn-photo-slot"[^>]*>(.*?)</div>', src, re.S)
    if not slot or slot.group(1) != expected_slot_inner:
        die("the image position must carry exactly the generic illustration "
            "and its one caption, and nothing else.")
    # G3b · THE SHARED v1.1 T2 RULES (preview_image_treatment.t2_problems):
    # every illustration pure inline vector, visibly labelled generic and not
    # an EcoSauna product, never named as the product, no rights narration.
    if pit.slot_treatment(src) != "T2":
        die("the image position is not a T2 generic illustration.")
    if len(pit.illustrations(src)) != len(ICONS) + 2:  # five cards, the slot, the hero
        die("every drawing must be marked as a generic illustration.")
    problems = pit.t2_problems(src, SUPPLIER)
    if problems:
        die("T2 illustration rules: " + "; ".join(problems))
    if "generic forms, not ecosauna products" not in low:
        die("the hero illustration is not labelled as generic.")

    # G3d · THE RIGHTS PROCESS IS NOT NARRATED.
    for phrase in ("where they would sit", "where your imagery would go",
                   "where your photography would", "stay yours until",
                   "images stay yours", "imagery waits until",
                   "until you tell us otherwise",
                   "before anything is published, so your", "your image here"):
        if phrase in low:
            die("the page narrates the image-rights process: %r." % phrase)

    # G6 · NO OTHER SUPPLIER'S CONTENT.
    for other in ("Cosy Cabins", "Hutsmith", "Yard Box", "Power Sheds",
                  "TRIQ", "BIOBUILDS", "Superior Pergola", "Honka",
                  "MyCabin", "Irish Sauna", "OGNYX", "TankTribe", "Tanktribe",
                  "Modulux", "Switch Electrical", "Sigenergy", "Auroom",
                  "Sauna Experts", "Hansa24"):
        if other in src:
            die("another supplier's content reached the page: " + other)

    # G7 · THE HOMEOWNER JOURNEY: all six steps, in order.
    found = re.findall(r'<li class="ev-step[^"]*"[^>]*><span class="ev-step-n">'
                       r'\d+</span><b>([A-Za-z]+)</b>', src)
    if tuple(found) != ("Discover", "Check", "Explore", "Compare", "Decide",
                        "Connect"):
        die("the homeowner journey is not the six frozen steps in order: %r"
            % (found,))

    # G8 · NO UNEVIDENCED CLAIM, NO BORROWED MARKETING.
    for phrase in BANNED_CLAIM_PHRASES:
        if phrase in low:
            die("the visible page makes a claim the first-party evidence does "
                "not support, or repeats the supplier's marketing as "
                "PlotNua's: %r." % phrase)
    # G8b · NATIONWIDE DELIVERY ATTRIBUTED, NOT ASSERTED.
    if "ecosauna say they deliver to all 32 counties" not in low:
        die("nationwide delivery must be attributed to EcoSauna in their name.")
    if "nationwide" in low:
        die("'nationwide' appears unattributed.")
    # G8c · THE PLANNING FIREWALL.
    if "local authority is the only body that can confirm" not in low:
        die("the planning firewall is missing.")
    # G8d · ESTIMATE STATUS, VAT, DELIVERY, INSTALLATION, WARRANTY: every
    # material qualification is on the page, not only in a closed panel.
    for need, why in (("not a quote", "starting prices are not quotes"),
                      ("estimate", "the configurator total is an estimate"),
                      ("vat is not stated", "VAT basis is unknown"),
                      ("do your prices include vat", "the VAT question"),
                      ("delivery charge", "delivery is charged by location"),
                      ("4 to 6 weeks", "the timescale is asked, attributed"),
                      ("warranty on each", "the warranty question"),
                      ("is it also offered for the hot tub", "installation question")):
        if need not in low:
            die("a material qualification is missing (%s)." % why)
    # G8e · The qualifications that sit at a glance are OUTSIDE any <details>.
    closed = re.sub(r"<details\b.*?</details>", " ", visible, flags=re.S)
    closed_low = re.sub(r"\s+", " ", closed).lower()
    for need in ("not a quote", "vat is not stated", "delivery charge",
                 "do your prices include vat", "warranty on each"):
        if need not in closed_low:
            die("the qualification %r is only inside a collapsed panel." % need)

    # G9 · NO SUPPLIER IMAGERY, PROVEN ON THE OUTPUT.
    for pattern, what in (
            (r'<img\b', "an <img>"),
            (r'<source[^>]+srcset=', "a <source>"),
            (r'url\(\s*["\']?https?://', "an external CSS url()"),
            (r'property="og:image"', "an og:image")):
        if re.search(pattern, src, re.I):
            die("the built page carries %s." % what)
    if "mapleapplehost" in src.lower() or "wp-content" in src.lower():
        die("a reference to EcoSauna's image hosting reached the page.")
    if 'href="%s' % SUPPLIER_SITE not in src:
        die("the page does not LINK back to %s." % SUPPLIER_SITE)
    if CREDIT not in src:
        die("the attribution line is missing the %r credit." % CREDIT)
    if 'href="%s"' % DISCOVERY_URL not in src:
        die("the Garden Retreat Discovery link is missing.")

    # G9b · NO DEAD LINKS. Every href is in-page and resolves, or is one of
    # the known destinations.
    allowed = {SUPPLIER_SITE, PRODUCTS_URL, WIZARD_URL, DISCOVERY_URL,
               PLOTNUA_URL}
    ids = set(re.findall(r'\bid="([^"]+)"', src))
    for href in re.findall(r'<a\b[^>]*\bhref="([^"]*)"', src):
        if href.startswith("#"):
            if href == "#" or href[1:] not in ids:
                die("a dead in-page link: %r" % href)
        elif href not in allowed:
            die("an unexpected link destination: %r" % href)

    # G10 · NO PARTNERSHIP, ENDORSEMENT OR COMMERCIAL MECHANISM.
    for word in ("partner", "approved supplier", "recommended", "trusted "
                 "supplier", "preferred supplier", "endorsed", "commission",
                 "exclusive", "affiliate", "sponsored", "advert",
                 "buy now", "add to basket", "checkout", "referral",
                 "get a quote", "request a quote", "enquire now"):
        if word in low:
            die("the page implies a relationship or mechanism that does not "
                "exist: " + word)
    if re.search(r"<form\b|<input\b|<textarea\b|<select\b", src, re.I):
        die("the page carries a form or input. No lead capture is active.")

    # G11 · THE PREVIEW SAYS WHAT IT IS; THE RANGE IS COMPLETE AND EXACT.
    for need in ("private supplier preview", "prepared for ecosauna",
                 "illustrative preview", "before anything goes live"):
        if need not in low:
            die("the page is missing %r." % need)
    if tuple(m["name"] for m in RANGE) != EXPECTED_PRODUCTS:
        die("the range does not match the five configurator products.")
    if tuple(m["name"] for m in RANGE if m["install"] is None) \
            != EXPECTED_NO_INSTALL_OPTION:
        die("an installation value appeared or disappeared that the "
            "configurator does not publish.")
    for m in RANGE:
        if m["from_eur"] != EXPECTED_FROM[m["name"]]:
            die("the starting price of %s is not the configurator's." % m["name"])
        if '<h3 id="p-%s-h">%s</h3>' % (m["key"], m["name"]) not in src:
            die("product %s is missing from the range." % m["name"])
        if '<span class="ev-from">From</span> %s' % eur(m["from_eur"]) not in src:
            die("the starting price of %s is missing from its card." % m["name"])
    n_tbc = sum(1 for m in RANGE if m["install"] is None)
    if visible.count(TBC_TEXT) != n_tbc:
        die("'%s' appears %d times for %d unpublished values."
            % (TBC_TEXT, visible.count(TBC_TEXT), n_tbc))

    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(src, encoding="utf-8")
    print("ECOSAUNA PRIVATE PREVIEW · v2 PREMIUM")
    print("=" * 74)
    print("  ok    25 guards passed")
    print("  ok    0 supplier images — state C; illustrations generic and inline")
    print("  ok    noindex, nofollow, noarchive, nosnippet, noimageindex")
    print("  ok    5 products, configurator prices exact; %d installation "
          "values to be confirmed" % n_tbc)
    print("  ok    every link resolves; no '#' link; inert controls marked")
    print("  ok    qualifications visible outside collapsed panels")
    print("  ok    no partnership, commission, form, testimonial, origin, "
          "health or planning claim; CONNECT_MODE none")
    print("-" * 74)
    print("wrote %s (%d bytes)" % (OUT, len(src.encode("utf-8"))))
    if STAGE:
        print("STAGED ONLY.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
