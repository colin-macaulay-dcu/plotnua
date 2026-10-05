#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DISC-026 . RESIDENTIAL COMPUTE EVIDENCE UPDATE . BOUNDED EDIT TO S3 AND S9.

Founder brief, 5 October 2026. New evidence materially strengthens S3: the
revelation is no longer only that computing makes useful heat, but that a
homeowner may not need to buy or run a miniature data centre at all — the home
may HOST part of a distributed one.

NOTHING STRUCTURAL CHANGES. Nine sections, same kickers, same type scale, same
five drawings, same eight drawers, no new <section>, no new imagery, no new
image-rights state. The energy anatomy and the wind position are not touched.
The held 6 October battery files are not opened.

*** WHAT RE-VERIFICATION FOUND, AND TWO THINGS IT RETIRED. ***

The brief said to re-check first-party before implementing. Doing so corrected
the brief's own summary twice and the page's existing copy twice.

1. "Installation approximately two hours" — NOT on heata.co today. The site
   describes the procedure in detail and gives no duration. Omitted entirely
   rather than carried as reported, because it adds nothing to the revelation.

2. "Household provides broadband" — true only of the pilot, and the page would
   have been misleading. heata's own FAQ: "We may connect to your broadband as
   part of a pilot but our broader plan is to install our own dedicated fibre
   or 4G / 5G connection as part of our wider rollout." The host gate today IS
   "a water cylinder and fast broadband". Both halves travel together.

3. RETIRED FROM THE PAGE: "a cylinder of roughly 425-450 mm diameter with
   clearance around it". Not findable on heata.co today. It came from the
   Stage 2 research pass and I could not re-confirm it, so it goes. What
   replaces it is what the site actually says: the thermal bridge is fitted to
   VENTED domestic hot water cylinders, and hosts need a cylinder and fast
   broadband.

4. RETIRED FROM THE PAGE: "Thermify HeatHub, deployed through the SHIELD trial
   with UK Power Networks", and the description of Thermify as a company that
   "pays for the electricity and sells the computing". That is heata's model,
   not Thermify's. Thermify's own site says HeatHub "replaces your home's
   traditional gas boiler", and the reported consumer model is a monthly
   household payment. Describing the two companies as the same model was the
   error this update exists to fix.

*** THE EVIDENCE TIERS, AND THEY ARE NOT THE SAME TIER. ***

FIRST-PARTY (heata.co, read 5 October 2026): patented thermal bridge on vented
cylinders · installation tested with British Gas engineers and checked against
cylinder manufacturers' warranties · heata pays the electricity, via an
accredited billing submeter · works ALONGSIDE the existing heating system ·
~4.8 kWh if it ran all day, lower in practice, "up to 80% of an average
household's hot water" with good utilisation · the GBP 340 figure is heata's
own calculation with its basis published · host gate is a cylinder and fast
broadband · there is a waitlist · hosts cannot run their own compute, it is
"really just an energy efficiency device" for them · a For Housing line exists.

FIRST-PARTY (thermify.cloud, read 5 October 2026): HeatHub replaces the gas
boiler · the Cloud network does "secure, decentralised data processing for
business customers" and captures the heat · an Early Adopter Programme seeking
10 organisations.

REPORTED ONLY, and labelled as such on the page or omitted: ~100 UK homes ·
~3,000 on the waitlist · one household's GBP 10-15 a month · Thermify's
~GBP 90 a month, bundled installation and lease, minimum ten-year term, and
unit sizes. The 14% / 34% / 15-year modelling figures are omitted entirely per
the brief.

NO ONE HOUSEHOLD'S SAVING BECOMES A GENERAL EXPECTATION. G-SAVE enforces it.

Run: python3 atlas-tools/build-disc026-residential-compute.py
"""

import hashlib
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
PAGE = ROOT / "discovery-house-as-power-station.html"

if not PAGE.exists():
    print("REFUSED: the Discovery is not in the tree")
    sys.exit(2)

html = PAGE.read_text(encoding="utf-8")
ORIGINAL = html


def die(msg):
    print("REFUSED: " + msg)
    sys.exit(2)


def anchored(text, old, new, label):
    n = text.count(old)
    if n != 1:
        die("anchor %r matched %d time(s), expected 1 -- nothing written"
            % (label, n))
    return text.replace(old, new)


# Fingerprint the two sections that must NOT change, whole.
def svg_at(text, marker):
    i = text.index(marker)
    return text[text.rindex("<svg", 0, i):text.index("</svg>", i) + 6]


ANAT = svg_at(html, "seven numbered positions: one, solar panels on the roof")
WIND = svg_at(html, "domestic wind turbine, drawn to scale at one metre")
ANAT_SHA = hashlib.sha256(ANAT.encode()).hexdigest()
WIND_SHA = hashlib.sha256(WIND.encode()).hexdigest()
WIND_POS = html[html.index("5 &middot; The open garden"):
                html.index("6 &middot; The driveway")]
WIND_POS_SHA = hashlib.sha256(WIND_POS.encode()).hexdigest()


# ===========================================================================
# S3 . THE LEDE AND THE MECHANISM.
# ===========================================================================

html = anchored(
    html,
    """    <h2>There are houses today with a computer bolted to the hot water cylinder.</h2>
    <span class="ev ev-emerging">Emerging &mdash; outside Ireland</span>
    <p>Not a prototype in a lab. Occupied homes, with a submeter on the wall and a
      box on the cylinder. The household gets the hot water.</p>
""",
    """    <h2>There are houses today with a computer bolted to the hot water cylinder.</h2>
    <span class="ev ev-emerging">Emerging &mdash; outside Ireland</span>
    <p>Not a prototype in a lab. Occupied homes, with a submeter on the wall and a
      box on the cylinder. The household gets the hot water.</p>

    <p>The chain is short enough to follow in one line. A business sends computing
      work to a server. The server does the work and, like every computer, turns
      almost all of its electricity into heat. That heat goes into the water in the
      cylinder. The company whose work it is pays for the electricity the server
      used. The house supplies the cylinder, the space and the connection.</p>

    <p><strong>Which means the homeowner isn&rsquo;t buying a miniature data
      centre. They are hosting part of one.</strong> heata is blunt about that: a
      host cannot run their own computing on the unit, because for the household it
      is, in their words, &ldquo;really just an energy efficiency device reducing
      your energy bill&rdquo;.</p>
""",
    "S3 lede and mechanism")


# ===========================================================================
# S3 . THE HEATA TILE. Corrected to what the site says today.
# ===========================================================================

html = anchored(
    html,
    """          <span class="dq-note">heata (Bit Warmer Ltd). The company&rsquo;s own
            modelling is 4.25&nbsp;kWh of hot water a day, up to
            &pound;340 a year. It needs a cylinder of roughly
            425&ndash;450&nbsp;mm diameter with clearance around it. British Gas
            ran a trial in employees&rsquo; homes.</span>""",
    """          <span class="dq-note">heata (Bit Warmer Ltd). The thermal bridge fits a
            <em>vented</em> cylinder, and the unit works alongside the existing
            heating system rather than replacing it. To host one, a home needs a
            water cylinder and fast broadband; there is a waiting list. heata&rsquo;s
            own figure is a saving of up to &pound;340 a year, calculated on
            4.25&nbsp;kWh of hot water a day at British energy prices. The
            installation was tested with British Gas engineers.</span>""",
    "S3 heata tile note")


# ===========================================================================
# S3 . THE THERMIFY TILE. It was describing heata's model. Corrected.
# ===========================================================================

html = anchored(
    html,
    """          <span class="dq-adv-label">Britain &middot; in homes</span>
          <span class="dq-fact">A household unit where the company pays for the
            electricity and sells the computing, and the heat stays in the
            house.</span>
          <span class="dq-note">Thermify HeatHub, deployed through the SHIELD
            trial with UK Power Networks. A second, independent household-scale
            precedent &mdash; which matters more than either one alone.</span>""",
    """          <span class="dq-adv-label">Britain &middot; proposed</span>
          <span class="dq-fact">A unit that <em>replaces</em> the gas boiler
            rather than working beside it, doing data processing for business
            customers and using that heat to warm the house and its water.</span>
          <span class="dq-note">Thermify HeatHub, in the company&rsquo;s own
            description. Reported, not published by them: a household price of
            around &pound;90 a month covering installation, the equipment lease and
            repairs, on a minimum ten-year term. Their open programme today is for
            ten organisations, not households.</span>""",
    "S3 Thermify tile")


# ===========================================================================
# S3 . THE TWO MODELS, AND WHY THE COMMERCIAL SHAPE IS THE POINT.
#      Placed after the UK/German bounding paragraph so nothing reads as an
#      Irish offer. Uses .dq-adv / .dq-adv-cols, which this section already
#      uses, at the default three columns. The third tile is not padding: it
#      is the thing both models share and the only part that is settled.
# ===========================================================================

html = anchored(
    html,
    """    <p style="margin-top:38px">Every one of those figures is British or German,
      under those countries&rsquo; electricity prices and programmes. None of it is open to an Irish homeowner. And in every
      case that is actually operating, what the household receives is
      <strong>heat</strong> &mdash; not income.</p>
""",
    """    <p style="margin-top:38px">Every one of those figures is British or German,
      under those countries&rsquo; electricity prices and programmes. None of it is open to an Irish homeowner. And in every
      case that is actually operating, what the household receives is
      <strong>heat</strong> &mdash; not income.</p>

    <p style="margin-top:38px">What has changed recently is not the physics. It is
      that two different <em>commercial</em> shapes have started to appear, and they
      ask opposite things of the household.</p>

    <div class="dq-adv">
      <span class="dq-cat dq-adv-cat">Two models, taking shape</span>
      <ul class="dq-adv-cols">
        <li>
          <span class="dq-adv-label">Host the compute</span>
          <span class="dq-fact">The provider owns the equipment and puts it in the
            house. The provider pays for the electricity it uses, and its heat helps
            heat the household&rsquo;s water.</span>
          <span class="dq-note">heata&rsquo;s model. The household pays nothing and
            gets heat; what it supplies is a suitable cylinder, the space and the
            connection. The existing heating system stays where it is.</span>
        </li>
        <li>
          <span class="dq-adv-label">Heating as a service</span>
          <span class="dq-fact">The computing equipment <em>is</em> the heating
            system, and the household pays a monthly amount for heat rather than
            buying a boiler.</span>
          <span class="dq-note">Thermify&rsquo;s proposed model. The reported price
            bundles installation, the equipment lease and repairs into a long
            contract. A proposition, not a service an Irish household can buy.</span>
        </li>
        <li>
          <span class="dq-adv-label">What both have in common</span>
          <span class="dq-fact">Neither asks the homeowner to buy a server, run it,
            or know anything about computing.</span>
          <span class="dq-note">In both models, the computing happens in the
            background. What matters to the household is much more familiar:
            whether the property can accommodate the equipment and make useful use
            of the heat.</span>
        </li>
      </ul>
    </div>

    <p style="margin-top:38px"><strong>The technology may be unfamiliar. The
      commercial idea isn&rsquo;t.</strong> Hosting equipment that somebody else
      owns and runs, or paying monthly for heat instead of buying the machine that
      makes it, are both arrangements Irish households already recognise from other
      parts of the house. If a residential compute proposition ever arrives here, it
      is more likely to look like one of those than like buying and running a
      server.</p>

    <p>Reported in September 2026, and worth holding lightly because it is reporting
      rather than a company statement: around a hundred UK homes have a heata unit,
      with roughly three thousand households on the waiting list and more
      installations planned. One of those households told a reporter their hot-water
      costs fell by about &pound;10&ndash;&pound;15 a month. That is one house, and
      it is not a figure anyone should expect.</p>
""",
    "S3 two models and the commercial shape")


# ===========================================================================
# S9 . THE PROPERTY-INTELLIGENCE CONSEQUENCE. Light touch, as instructed.
# ===========================================================================

html = anchored(
    html,
    """    <p>It keeps four kinds of finding apart""" if False else
    """    <p><strong>It will not give you a score.</strong> We can&rsquo;t give a property
      a meaningful percentage yet, because nobody has established what a fully
      &ldquo;compute-ready&rdquo; home would actually require. And
      <em>&ldquo;I don&rsquo;t know&rdquo;</em> is a real answer to every question in
      it &mdash; it costs you nothing to say so.</p>
""",
    """    <p><strong>It will not give you a score.</strong> We can&rsquo;t give a property
      a meaningful percentage yet, because nobody has established what a fully
      &ldquo;compute-ready&rdquo; home would actually require. And
      <em>&ldquo;I don&rsquo;t know&rdquo;</em> is a real answer to every question in
      it &mdash; it costs you nothing to say so.</p>

    <p>What we can say is roughly what the questions would be about. Not whether you
      want a data centre. Things much more ordinary: how your water is heated and
      what kind of cylinder you have, your broadband, your electrical supply, where
      equipment could sit, and how much hot water the household actually uses. The
      British examples above turn on exactly those details.</p>

    <p>Those ordinary facts about a house may eventually decide whether it can host
      something much less ordinary. <strong>They are not a checklist, and they are
      not every provider&rsquo;s criteria</strong> &mdash; two companies already
      want different things. But they are the kind of thing worth knowing about your
      own home either way.</p>
""",
    "S9 property-intelligence consequence")


# ===========================================================================
# ASSERTIONS
# ===========================================================================

checks = []


def must(cond, label):
    checks.append((bool(cond), label))


visible = re.sub(r"<!--[\s\S]*?-->", " ", html)
visible = re.sub(r"<(script|style)[\s\S]*?</\1>", " ", visible)
low = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", visible)).lower()

# ---- the revelation and the mechanism are present -------------------------
must("hosting part of one" in low, "the key revelation is on the page")
must("really just an energy efficiency device" in low,
     "heata's own words carry the revelation, not PlotNua's paraphrase")
must("the technology may be unfamiliar. the commercial idea isn" in low,
     "the commercial-familiarity line is present")
for step in ("sends computing", "turns\n      almost all of its electricity into heat"
             if False else "almost all of its electricity into heat",
             "that heat goes into the water in the", "pays for the electricity the server"):
    must(step.lower() in low or step in html, "mechanism step present: %s" % step[:40])

# ---- the two models are distinguished, not conflated ---------------------
must("Host the compute" in html and "Heating as a service" in html,
     "both models are named")
must("What both have in common" in html, "the shared ground is stated")
must("the computing happens in the\n            background" in html,
     "the corrected shared-ground explanation is present")
must("somebody else owns the work" not in html,
     "the retired ownership phrasing is gone")
must("replaces</em> the gas boiler" in html,
     "Thermify is described as replacing the boiler, which is its own wording")
must("works alongside the existing\n            heating system rather than replacing it" in html,
     "heata is described as working alongside, which is its own wording")
must("SHIELD" not in html, "the unverifiable SHIELD claim is retired")
must("425" not in html and "450&nbsp;mm" not in html,
     "the unverifiable cylinder-diameter figure is retired")

# ---- EVIDENCE TIERING. Reported figures must be labelled as reported. ----
must("Reported, not published by them" in html,
     "Thermify's price and term are labelled as reported")
must("it is reporting\n      rather than a company statement" in html,
     "the 100 / 3,000 figures are labelled as reporting")
must("That is one house, and" in html,
     "the single household's saving is bounded to that house")
must("not a figure anyone should expect" in low,
     "no general expectation is created from one household")
# the 14 / 34 / 15-year modelling figures were ordered omitted
for omitted in ("14%", "34%", "15-year", "fifteen-year"):
    must(omitted not in html, "omitted modelling figure absent: %s" % omitted)
# the unverifiable two-hour install
must("two hours" not in low and "2 hours" not in low,
     "the unverifiable installation duration is absent")

# ---- heata's own figure keeps its basis ----------------------------------
must("calculated on" in low and "4.25&nbsp;kWh" in html,
     "the GBP 340 figure carries its basis")
must("at British energy prices" in html,
     "the saving is bounded to British prices")

# ---- GOVERNANCE BOUNDARIES ----------------------------------------------
must("None of it is open to an Irish homeowner" in html,
     "the Irish-availability bound survives")
must("not a service an Irish household can buy" in html,
     "Thermify is explicitly not available here")
for ireland in ("heata in Ireland", "heata Ireland", "Thermify Ireland",
                "available in Ireland through", "coming to Ireland"):
    must(ireland.lower() not in low, "no Irish-operation implication: %r" % ireland)
for rel in ("our partner", "partnership with heata", "partnership with Thermify",
            "working with heata", "working with Thermify",
            "PlotNua and heata", "acquisition partner"):
    must(rel.lower() not in low, "no PlotNua relationship implied: %r" % rel)
must("Tandem has confirmed that individual homes are not part of its current"
     in html, "the Tandem bound is untouched")
must("Distributed residential computing is not currently commercially" in html,
     "RCR finding 1 untouched")
must("no one can tell you whether a property is technically" in html,
     "RCR finding 2 untouched")
# S9 must not claim an assessment capability
must("not a checklist, and they are" in html,
     "S9 states these are not a checklist")
must("not every provider" in low, "S9 states these are not universal criteria")
for overclaim in ("we can assess", "we can tell you whether your home can host",
                  "plotnua can assess"):
    must(overclaim not in low, "no suitability-assessment claim: %r" % overclaim)

# ---- NOTHING STRUCTURAL MOVED -------------------------------------------
must(hashlib.sha256(svg_at(html, "seven numbered positions: one, solar panels on "
                                 "the roof").encode()).hexdigest() == ANAT_SHA,
     "energy anatomy drawing byte-identical (%s)" % ANAT_SHA[:12])
must(hashlib.sha256(svg_at(html, "domestic wind turbine, drawn to scale at one "
                                 "metre").encode()).hexdigest() == WIND_SHA,
     "wind drawing byte-identical (%s)" % WIND_SHA[:12])
must(hashlib.sha256(html[html.index("5 &middot; The open garden"):
                         html.index("6 &middot; The driveway")].encode()
                    ).hexdigest() == WIND_POS_SHA,
     "the whole wind position byte-identical (%s)" % WIND_POS_SHA[:12])
must(html.count("<svg") == ORIGINAL.count("<svg") == 5, "still five drawings")
must(html.count("<section") == ORIGINAL.count("<section"), "no section added")
must(html.count("<details") == ORIGINAL.count("<details") == 8, "still eight drawers")
must(html.count('class="pos-eq"') == 7, "seven anatomy positions untouched")
must(html.count('class="imgnote"') == 4, "four image notes, none added")
must(len(re.findall(r'<img ', html)) == len(re.findall(r'<img ', ORIGINAL)),
     "no image element added")
must(not re.findall(r'<img[^>]+src="https?://', html), "no remote imagery")
AMT = re.compile(r"&euro;(\d{1,3}(?:,\d{3})*)")
must(set(AMT.findall(ORIGINAL)) == set(AMT.findall(html)),
     "the governed euro set is unchanged")
must("From 6 October 2026 SEAI is to pay a flat" in html,
     "the battery boundary is untouched")
must(html.count("PN-DISC026-BATTERY-BOUNDARY-BEGIN") == 1,
     "battery boundary markers untouched")
must(html.count("<main") == html.count("</main>"), "main balanced")
must(html.count("<div") == html.count("</div>"), "div balanced")

bad = [lab for ok, lab in checks if not ok]
print("DISC-026 . RESIDENTIAL COMPUTE EVIDENCE UPDATE")
print("=" * 74)
for ok, lab in checks:
    print("  %s  %s" % ("PASS" if ok else "FAIL", lab))
print("=" * 74)
if bad:
    print("REFUSED -- %d assertion(s) failed. Nothing written." % len(bad))
    sys.exit(2)

PAGE.write_text(html, encoding="utf-8")
print("WROTE %s (%d checks passed, %d -> %d bytes)"
      % (PAGE.name, len(checks), len(ORIGINAL), len(html)))
