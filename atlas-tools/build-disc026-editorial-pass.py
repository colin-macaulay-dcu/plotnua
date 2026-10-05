#!/usr/bin/env python3
"""
DISC-026 . FOUNDER REVIEW CORRECTIONS . BOUNDED EDITORIAL PASS
===========================================================================
Six corrections from the founder review of 4 October 2026. This is an
EDITORIAL pass: no redesign, no new research, no change to the evidence base,
and not one evidence claim widened.

  1  INTERNAL GOVERNANCE LANGUAGE OUT OF HOMEOWNER COPY. "a build gate stops
     a number reaching the page", "emitted on every single run", the
     three-states/four-finding-types machinery. The limitation stays, in
     natural English. The discipline stays in the code and the guards.
  2  THE SEVEN POSITIONS BECOME THE SURFACE. Each one leads with its idea --
     sun to electricity, battery to stored electricity -- in the page's
     largest type. Grants, MPRN, NC6, planning, noise and tax move into a
     per-position drawer built on the page's own .faq-item.is-inline
     component. Nothing is deleted; it is demoted.
  3  THE GROUND-SOURCE REVELATION IS RESTORED. Cooling returns as a concept,
     conditioned on system, ground and design. It is NOT claimed that an
     Irish domestic installation will deliver it. The precise Irish evidence
     limitation stays in the drawer.
  4  THE IRISH-OPERATOR GENERALISATION IS CORRECTED. We have direct evidence
     about Tandem, not about every Irish operator. Every generalisation from
     one to all is replaced with the bounded formulation.
  5  IMAGE-RIGHTS PLACEHOLDERS ARE QUIETENED. One short editorial caption.
     The correspondence workflow is not homeowner copy. UNKNOWN still fails
     closed internally -- that is the gate's job, not the reader's problem.
  6  THE STORY IS PRESERVED. Compute in homes abroad -> Tallaght ->
     an Irish operator at commercial and community scale -> the property's
     own energy anatomy -> the future home-scale possibility. The flagship is
     untouched.

EVERY ANCHOR MUST MATCH EXACTLY ONCE or the build refuses with sys.exit(2)
and writes nothing. A second run also refuses. The anatomy FIGURE is lifted
verbatim out of the page rather than retyped, so the diagram cannot drift by
transcription.

Run: python3 atlas-tools/build-disc026-editorial-pass.py
"""

import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
PAGE = ROOT / "discovery-house-as-power-station.html"


def die(msg):
    print("REFUSED: " + msg)
    sys.exit(2)


if not PAGE.exists():
    die("the Discovery is not in the tree")

html = PAGE.read_text(encoding="utf-8")
BEFORE_LEN = len(html)


def anchored(text, old, new, expect=1, label=""):
    n = text.count(old)
    if n != expect:
        die("anchor %r matched %d time(s), expected %d -- nothing written"
            % (label or old[:60], n, expect))
    return text.replace(old, new)


# ---------------------------------------------------------------------------
# CSS . Two components, on the tokens the page already defines.
# ---------------------------------------------------------------------------

CSS = """
  /* ==================================================================
     FOUNDER REVIEW CORRECTIONS, 4 October 2026.

     .pos-eq   the seven positions ARE the revelation, so each one now
               leads with its idea in the largest type on the page --
               larger than the section heading. Light weight, because at
               this size weight would shout where scale is enough.
     .imgnote  one quiet line where a real photograph will go. The
               permission workflow is ours, not the reader's.
     ================================================================== */

  .pos-eq{ display:block; font-family:'Fraunces',Georgia,serif;
    font-weight:300; font-size:clamp(27px,4.4vw,48px); line-height:1.08;
    letter-spacing:-.022em; color:var(--ink); margin:0 0 18px; }
  .pos-eq i{ font-style:normal; color:var(--accent); padding:0 .14em;
    font-weight:300; }
  /* the one-idea sentence steps down hard, so the idea above it leads */
  .pos h3{ font-family:'Fraunces',Georgia,serif; font-weight:500;
    font-size:clamp(17px,1.7vw,19px); line-height:1.38; margin:0 0 12px;
    color:var(--ink); max-width:46ch; }
  .pos .faq-item.is-inline{ margin-top:20px; }
  .pos .faq-item.is-inline summary h3{ font-size:14.5px; max-width:none; }

  .imgnote{ display:block; margin:22px 0 0; font-family:'Work Sans',sans-serif;
    font-size:11.5px; line-height:1.7; letter-spacing:.01em;
    color:var(--soft); }

  @media (max-width:760px){
    .pos-eq{ font-size:clamp(24px,7.4vw,30px); }
  }
"""

html = anchored(html, "\n</style>", "\n" + CSS + "\n</style>", 1, "CSS insert")


# ---------------------------------------------------------------------------
# 1 . S9 . THE GOVERNANCE LANGUAGE COMES OUT.
# ---------------------------------------------------------------------------

OLD_S9 = """    <p>There is a separate check that reads a property against what PlotNua can
      actually stand over, and tells you what is still to establish. It gives
      <strong>three states and no score</strong>, because a percentage would claim we
      know what 100% means. We do not, and a build gate stops a number reaching the
      page.</p>
    <p>It keeps four kinds of finding apart &mdash; what is present, what the gaps
      are, what is simply absent, and what is conditional &mdash; and
      <em>&ldquo;I don&rsquo;t know&rdquo;</em> is a real answer to every question in
      it. The two findings in the dark band above are emitted on every single run,
      whatever anyone answers.</p>"""
NEW_S9 = """    <p>There is a separate check that walks through your property and tells you
      what is already there, what is missing, and what nobody can answer yet.</p>
    <p><strong>It will not give you a score.</strong> We can&rsquo;t give a property
      a meaningful percentage yet, because nobody has established what a fully
      &ldquo;compute-ready&rdquo; home would actually require. And
      <em>&ldquo;I don&rsquo;t know&rdquo;</em> is a real answer to every question in
      it &mdash; it costs you nothing to say so.</p>"""
html = anchored(html, OLD_S9, NEW_S9, 1, "S9 governance language")


# ---------------------------------------------------------------------------
# 4 . THE IRISH-OPERATOR GENERALISATION. One occurrence on the page; the
#     guard added alongside this build refuses any other.
# ---------------------------------------------------------------------------

OLD_CHAIN5 = ("<span>Operating in British and German homes. Not available in "
              "Ireland, and not on any Irish operator&rsquo;s pipeline for homes "
              "today.</span>")
NEW_CHAIN5 = ("<span>Operating in homes abroad. PlotNua has not found an equivalent "
              "Irish residential offering, and Tandem has confirmed that individual "
              "homes are not part of its current pipeline.</span>")
html = anchored(html, OLD_CHAIN5, NEW_CHAIN5, 1, "chain 05 generalisation")

OLD_CHAIN6 = ("<span>Real at district scale in Tallaght since 2023. Real at "
              "household scale abroad. Not connected to an Irish house by "
              "anyone.</span>")
NEW_CHAIN6 = ("<span>Real at district scale in Tallaght since 2023. Real at "
              "household scale abroad. PlotNua has found no Irish house connected "
              "to it.</span>")
html = anchored(html, OLD_CHAIN6, NEW_CHAIN6, 1, "chain 06 generalisation")


# ---------------------------------------------------------------------------
# 5 . THE IMAGE-RIGHTS PLACEHOLDERS. Four long operational notes become one
#     short editorial line each. The wind one keeps the fact that the diagram
#     is to the rule's own scale, because that IS homeowner information.
# ---------------------------------------------------------------------------

CAPTION = "Real installation photography will be added when publication rights are confirmed."

RIGHTS_BLOCKS = [
    # S3 . heata
    ("""<div class="rights">
      <b>A photograph belongs here and there isn&rsquo;t one yet.</b> The useful
      image is a compute unit on a real domestic cylinder, which would bound this
      idea honestly in a single frame. PlotNua has asked heata for permission and
      has not had an answer. Until permission is given, this position stays empty:
      we will not illustrate a real installation with a picture we generated.
    </div>""",
     '<span class="imgnote">' + CAPTION + '</span>'),
    # S4 . Codema
    ("""<div class="rights">
      <b>Photographs requested, not yet granted.</b> The images that would carry
      this &mdash; the energy centre, the campus buildings on the network, the
      apartments &mdash; belong to Codema, South Dublin County Council and Heat
      Works. PlotNua has written to Codema and is waiting. Irish proof has to be
      photographic or absent, so it is absent for now.
    </div>""",
     '<span class="imgnote">' + CAPTION + '</span>'),
]
for old, new in RIGHTS_BLOCKS:
    html = anchored(html, old, new, 1, "rights block -> imgnote")


# ---------------------------------------------------------------------------
# 2 . THE ENERGY ANATOMY. The surface is rebuilt; the figure is lifted
#     verbatim from the page so the diagram cannot drift.
# ---------------------------------------------------------------------------

FIG_START = '      <div class="anat-fig">\n        <svg viewBox="0 0 900 400"'
FIG_END = ('        <p class="anat-cap">Seven positions, drawn by PlotNua. Which of '
           'them apply')
if html.count(FIG_START) != 1 or html.count(FIG_END) != 1:
    die("could not locate the anatomy figure uniquely")
fs = html.index(FIG_START)
fe = html.index("      </div>", html.index(FIG_END)) + len("      </div>")
FIGURE = html[fs:fe]
if "<svg" not in FIGURE or "</svg>" not in FIGURE or len(FIGURE) < 2000:
    die("the lifted anatomy figure does not look like the figure")

ANAT_START = '    <div class="anat">'
ANAT_END = '    <details class="faq-item is-inline" style="margin-top:44px">'
if html.count(ANAT_START) != 1 or html.count(ANAT_END) != 1:
    die("could not locate the anatomy block uniquely")
a = html.index(ANAT_START)
b = html.index(ANAT_END)
if b <= a:
    die("the anatomy block anchors are in the wrong order")

OLD_ANAT = html[a:b]
# Everything demoted must still be on the page afterwards. Sampled, not
# assumed: these are the facts the founder asked to move, not remove.
MUST_SURVIVE = [
    "&euro;700 per kWp", "&euro;200 for each additional kWp", "&euro;1,800",
    "0% VAT", "no limit on the roof area", "Architectural Conservation Area",
    "before 2021",
    "From 6 October 2026 SEAI is to pay a flat", "before 2025",
    "microgenerator", "NC6", "&euro;14,500", "2.3",
    "13&nbsp;m", "6&nbsp;m rotor", "3&nbsp;m clearance",
    "43&nbsp;dB(A)", "special amenity area order", "Section 5 Declaration",
    "&euro;80", "small wind turbines", "two million smart meters",
    "&euro;400 a year", "offered and refused",
    "EN&nbsp;50549", "I.S.&nbsp;10101", "EN&nbsp;ISO&nbsp;15118",
    "Safe Electric", "Wind Atlas", "50&nbsp;m",
]

NEW_ANAT = r"""    <div class="anat">
""" + FIGURE + r"""

      <!-- ====================================================================
           THE SEVEN POSITIONS. Founder review correction 2: the positions are
           the revelation, so each one leads with its idea in the largest type
           on the page -- larger than the section heading above it.

           THE DETAIL IS DEMOTED, NOT DELETED. Grants, MPRN, NC6, planning,
           noise and tax now sit in a per-position drawer on the page's own
           .faq-item.is-inline component. The build asserts that every one of
           those facts is still present afterwards: a homeowner who wants the
           detail is one click away, and nothing was quietly dropped in the
           name of simplicity.
           ==================================================================== -->

      <!-- 1 . ROOF -->
      <div class="pos">
        <span class="pos-where">1 &middot; Roof</span>
        <span class="pos-eq">Sun <i>&rarr;</i> electricity</span>
        <span class="ev">Today</span>
        <h3>The one position almost every house already has.</h3>
        <p>Panels turn daylight into electricity the house uses as it is made. No
          moving parts, no planning permission on a house, and the State pays part
          of the cost.</p>
        <details class="faq-item is-inline">
          <summary><h3>Grant, VAT and permission</h3><span class="icon"></span></summary>
          <div class="faq-a"><strong>The grant.</strong> &euro;700 per kWp for the
            first 2&nbsp;kWp, then &euro;200 for each additional kWp up to
            4&nbsp;kWp, paid pro rata &mdash; a maximum of &euro;1,800 in 2026.
            SEAI.<br><br>
            <strong>VAT.</strong> 0% on the supply and installation of panels on a
            private dwelling.<br><br>
            <strong>Who qualifies.</strong> The home must have been built and
            occupied before 2021. The grant is not open where solar PV funding has
            already been claimed at that MPRN &mdash; whoever claimed it. Your
            installer applies to ESB Networks before anything goes on the roof, and
            that usually takes at least four weeks; afterwards the house needs a new
            BER assessment before the grant is paid.<br><br>
            <strong>Permission.</strong> No planning permission for rooftop panels on
            a house, and no limit on the roof area used. Restrictions still apply to
            protected structures and homes in an Architectural Conservation Area, and
            the exemption carries conditions such as a minimum distance from the roof
            edge.<br><br>
            <strong>Who stands behind the work.</strong> SEAI&rsquo;s own words: it
            &ldquo;does not approve, guarantee, or warranty a company or their
            works.&rdquo; The State pays part of the cost. Choosing the installer is
            still entirely yours.</div>
        </details>
      </div>

      <!-- 2 . UTILITY / WALL -->
      <div class="pos">
        <span class="pos-where">2 &middot; Utility room, garage or wall space</span>
        <span class="pos-eq">Battery <i>&rarr;</i> stored electricity</span>
        <span class="ev">Today</span>
        <h3>A battery doesn&rsquo;t make electricity. It moves it through time.</h3>
        <p>It holds the afternoon until the evening. This is the piece that turns a
          house from something that reacts to the grid into something that can
          choose.</p>
        <details class="faq-item is-inline">
          <summary><h3>Grant, eligibility and the grid side</h3><span class="icon"></span></summary>
          <div class="faq-a">
            <!-- PN-DISC026-BATTERY-BOUNDARY-BEGIN
                 THE GOVERNED DATE BOUNDARY, carried into the drawer unchanged.
                 Stated in ANNOUNCED form with the date on its face, so the
                 sentence is true before 6 October 2026 and true after it.
                 Converting it to the present tense on or after that date is a
                 single anchored edit INSIDE these markers and is deliberately
                 not part of this build. Do not remove the markers; they are
                 what makes that edit bounded. -->
            <strong>The grant.</strong> From 6 October 2026 SEAI is to pay a flat
            &euro;600 towards a home battery of 5&nbsp;kWh or larger. Batteries under
            5&nbsp;kWh are not eligible, and the amount is flat rather than scaled to
            size.
            <!-- PN-DISC026-BATTERY-BOUNDARY-END --><br><br>
            <strong>Who qualifies.</strong> The home needs an MPRN and must have been
            built and occupied <em>before 2025</em> &mdash; a different year from the
            solar grant, which is why a house finished in 2022 can be outside one and
            inside the other. One per MPRN, installed by an SEAI registered Solar PV
            contractor, with the ESB Networks application made before installation.
            Solar and battery can go in a single application.<br><br>
            <strong>The grid side.</strong> ESB Networks treats an AC-connected
            battery as a microgenerator, listed on the NC6 application with its rated
            output, within the microgeneration thresholds and assessed on inverter
            capacity. The notification happens before installation, not after, and
            the work is certified by a Safe Electric registered electrician.<br><br>
            <strong>Two things we have not established.</strong> Whether a battery
            installed before that date can be claimed retrospectively, and how the
            &euro;600 interacts with the solar grant ceiling. We will not guess at
            either.</div>
        </details>
      </div>

      <!-- 3 . AIR -->
      <div class="pos">
        <span class="pos-where">3 &middot; The air beside the house</span>
        <span class="pos-eq">Heat pump <i>&rarr;</i> heat from outside</span>
        <span class="ev">Today</span>
        <h3>There is usable heat in Irish air, even in February.</h3>
        <p>A unit about the size of a small chest freezer takes it out of the air and
          moves it inside. It is the largest single change most Irish houses can make
          to how they use energy &mdash; and the one that most changes what the roof
          and the battery are for.</p>
        <div class="pos-open">One condition decides it: <strong>the house has to be
          able to hold the heat first.</strong> A heat pump in a house that leaks heat
          is an expensive way to be cold, which is exactly why the test below
          exists.</div>
        <details class="faq-item is-inline">
          <summary><h3>Grant and the heat loss test</h3><span class="icon"></span></summary>
          <div class="faq-a"><strong>The grant.</strong> Up to &euro;14,500 as a
            bundle for a detached, semi-detached or mid-terrace house. The ceiling is
            lower for an apartment, and lower again for air-to-air. SEAI.<br><br>
            <strong>The test.</strong> SEAI uses a Heat Loss Indicator of 2.3 or
            below. If your house is above it, or nobody knows, a technical assessment
            establishes the position. The home must have been built and occupied
            before 2021.</div>
        </details>
      </div>

      <!-- 4 . GROUND . Founder review correction 3: the revelation is restored.
           The CONCEPT of cooling returns, conditioned on system, ground and
           design. It is NOT claimed that an Irish domestic installation will
           deliver it; the precise evidence limitation is in the drawer. -->
      <div class="pos">
        <span class="pos-where">4 &middot; The ground beneath the garden</span>
        <span class="pos-eq">Ground <i>&rarr;</i> heat from below</span>
        <span class="ev">Today</span>
        <h3>The ground can do more than heat a house.</h3>
        <p>A few metres down, the ground sits at roughly the same temperature all
          year. A ground-source system draws that relatively stable heat from beneath
          the property &mdash; through pipework laid in shallow trenches across the
          garden, or down a borehole where there is no room to dig.</p>
        <p>Some systems can also use that same ground connection for cooling. Whether
          that works for a particular Irish home depends on the system, the ground
          conditions and the design.</p>
        <details class="faq-item is-inline">
          <summary><h3>Grant, what decides it, and what we have not established</h3><span class="icon"></span></summary>
          <div class="faq-a"><strong>The grant.</strong> The same &euro;14,500
            ceiling as an air-to-water system, and water-to-water likewise.
            Ground-source is not a separate scheme and is not funded differently
            &mdash; it sits inside the same heat pump grant. SEAI.<br><br>
            <strong>What decides it.</strong> Garden area for trenches, or access for
            a drilling rig. This is the one position where the shape of the site,
            rather than the house, is the constraint.<br><br>
            <strong>On cooling.</strong> PlotNua has not established, from a
            first-party Irish source, whether or on what terms a domestic ground loop
            in Ireland can be used for cooling. The capability is real in the
            technology; the Irish domestic position is not something we can stand over
            yet, and we will say so plainly when we can.</div>
        </details>
      </div>

      <!-- 5 . GARDEN . Administrative possibility and site suitability stay
           visibly separated. Founder correction 2 of the previous review
           withdrew a sentence characterising the air at the exempt rotor
           height; the evidence does not establish it to the required standard,
           so it is not in this page and not quoted in this comment either. -->
      <div class="pos">
        <span class="pos-where">5 &middot; The open garden</span>
        <span class="pos-eq">Wind <i>&rarr;</i> another possible source</span>
        <span class="ev">Today &mdash; legally and administratively</span>
        <h3>You can put up a wind turbine in Ireland without planning permission.</h3>
        <p>Inside a tight envelope, connected under the same rules as solar, and paid
          for what it exports. That is genuinely true &mdash; and it is only half the
          question.</p>
        <div class="pos-open"><strong>What is settled is what you may build and
          connect. What is not settled is whether it would be worth building at your
          property.</strong> PlotNua has not established realistic output, turbulence
          from surrounding buildings and trees, installation and maintenance costs, or
          credible Irish suppliers &mdash; and we will not estimate any of them from
          vendor material.<br><br>
          The one number most likely to decide it for you is the boundary rule. The
          mast has to stand back from the nearest party boundary by the full height of
          the assembly plus a metre &mdash; a 14&nbsp;m clear radius at the maximum
          exempt size, which rules out a great many suburban gardens before wind is
          discussed at all.</div>
        <details class="faq-item is-inline">
          <summary><h3>The exempt envelope, in full</h3><span class="icon"></span></summary>
          <div class="faq-a"><strong>Size.</strong> 13&nbsp;m total height.
            6&nbsp;m rotor. 3&nbsp;m clearance between the ground and the lowest
            point of the blades. One per house, not attached to the building, not
            sited in front of it. Matt finish, no advertising, no interference with
            telecoms signals. SEAI, summarising S.I.&nbsp;83 of 2007 and
            S.I.&nbsp;235 of 2008.<br><br>
            <strong>Setback.</strong> The mast must stand back from the nearest party
            boundary by the total height of the assembly plus one metre.<br><br>
            <strong>Noise.</strong> 43&nbsp;dB(A) or less, or no more than
            5&nbsp;dB(A) above background, at the nearest inhabited neighbouring
            dwelling.<br><br>
            <strong>Where the exemption disappears.</strong> It does not apply at all
            where the work would affect a protected landscape or view, protected
            archaeological, geological, historical, scientific or ecological features,
            or an area under a special amenity area order. Designations change under a
            house. SEAI advises a Section 5 Declaration from the local authority,
            about &euro;80, and warns: &ldquo;There have been instances of people
            assuming they were exempt which have ended with the local authority
            requesting that installations be removed.&rdquo;<br><br>
            <strong>Connecting it.</strong> ESB Networks&rsquo; micro-generation
            definition &ldquo;makes no explicit reference to any specific form of
            generating technology&rdquo;, so a domestic turbine goes through the same
            NC6 route as solar. Micro-generation is 25&nbsp;A or less on a single
            phase, about 6&nbsp;kVA. Where generation is not inverter-connected
            &mdash; which small wind can be &mdash; capacity is assessed on the
            generator&rsquo;s own continuous rating.<br><br>
            <strong>Being paid for it.</strong> The regulator&rsquo;s definition of
            microgeneration names small wind turbines explicitly, so export is paid on
            the same terms as solar. CRU. There is <strong>no SEAI grant</strong> for
            a domestic wind turbine.<br><br>
            <strong>Two cautions.</strong> The SEAI Wind Atlas is the obvious place to
            look and <strong>it cannot answer this question</strong>: its lowest
            height is 50&nbsp;m, and the tallest exempt domestic turbine is
            13&nbsp;m. And the SEAI document that sets out these exemptions is
            demonstrably out of date on solar, so the wind rule should be confirmed
            against current legislation before anyone relies on it.</div>
        </details>
        <span class="imgnote">The diagram above is drawn to the rule&rsquo;s own
          scale. Real installation photography will be added when publication rights
          are confirmed.</span>
      </div>

      <!-- 6 . DRIVEWAY -->
      <div class="pos">
        <span class="pos-where">6 &middot; The driveway</span>
        <span class="pos-eq">EV <i>&rarr;</i> transport today, maybe storage next</span>
        <span class="ev">Today &mdash; charging</span>
        <h3>A car is a battery that happens to have wheels.</h3>
        <p>Charging at home needs somewhere off-street to put it, and that is the
          whole of the test. Moving the charging to whichever hours your supplier
          prices lowest costs nothing and changes the bill.</p>
        <div class="pos-open">The interesting direction is the other one: the car
          powering the house, or the grid. <strong>PlotNua has not established when, or
          whether, a homeowner can actually buy that in Ireland.</strong> You will find
          confident dates for it online. We could not stand over any of them, so we are
          not repeating them.</div>
        <details class="faq-item is-inline">
          <summary><h3>What ESB Networks has published about two-way charging</h3><span class="icon"></span></summary>
          <div class="faq-a">ESB Networks treats a car exporting to the grid as a
            generator, under the same micro-generation and mini-generation rules as
            solar, a battery or a turbine. It has published the architecture and
            standards it expects, including EN&nbsp;50549 with Irish protection
            settings, I.S.&nbsp;10101, EN&nbsp;ISO&nbsp;15118 for the vehicle
            interface and Safe Electric certification &mdash; and says to apply for
            the generator connection <em>before</em> choosing the car and charger
            combination.<br><br>
            What that document does not establish is availability. It is the
            architecture, not a date.</div>
        </details>
      </div>

      <!-- 7 . GRID -->
      <div class="pos">
        <span class="pos-where">7 &middot; The grid connection</span>
        <span class="pos-eq">Export <i>&rarr;</i> the house becomes a participant</span>
        <span class="ev">Today</span>
        <h3>The position nobody thinks of as part of the house.</h3>
        <p>It is the piece that turns the other six from a private arrangement into
          something the system can see, use and pay for. Over two million smart meters
          are installed in Ireland, and more than four out of five households have
          one.</p>
        <details class="faq-item is-inline">
          <summary><h3>Meter, export, tax &mdash; and one trap</h3><span class="icon"></span></summary>
          <div class="faq-a"><strong>The meter.</strong> Over two million smart meters
            are installed and more than four out of five households have one. ESB,
            September 2025. Having one does not put you on a time-of-use tariff
            &mdash; that is a separate choice with your supplier.<br><br>
            <strong>Export.</strong> Every electricity supplier must pay for eligible
            electricity you export &mdash; but not until the NC6 or NC7 has been
            processed by ESB Networks. Without that, the supplier will not pay. Rates
            are not regulated; each supplier sets its own.<br><br>
            <strong>Tax.</strong> The first &euro;400 a year of microgeneration income
            is exempt from income tax.<br><br>
            <strong>The trap.</strong> If a smart meter has been offered and refused,
            the home is not eligible for export payment at all. Worth checking if
            anybody in the house ever said no at the door.</div>
        </details>
      </div>
    </div>

"""

html = html[:a] + NEW_ANAT + html[b:]

# ---------------------------------------------------------------------------
# 5b . The S7 closing rights note, after the anatomy was rebuilt.
# ---------------------------------------------------------------------------

OLD_S7_RIGHTS = """<div class="rights">
      <b>Why there are no photographs of real Irish installations here yet.</b> Every
      position above deserves one &mdash; a real roof, a real battery on a real
      utility wall, a trench with a ground loop in it, a charger on a real driveway.
      PlotNua does not publish a supplier&rsquo;s photograph because it is visible on
      their website. Permission requests are out and unanswered, and until they come
      back these positions carry a diagram or nothing. The page is built so that a
      granted photograph drops into its position without anything else moving.
    </div>"""
html = anchored(html, OLD_S7_RIGHTS,
                '<span class="imgnote">' + CAPTION + '</span>',
                1, "S7 rights block -> imgnote")


# ---------------------------------------------------------------------------
# ASSERTIONS.
# ---------------------------------------------------------------------------

checks = []


def must(cond, label):
    checks.append((bool(cond), label))


# 1 . no implementation language left in homeowner copy
visible = re.sub(r"<!--[\s\S]*?-->", "", html)
visible = re.sub(r"<(script|style)[\s\S]*?</\1>", "", visible)
for phrase in ("build gate", "emitted on every", "three states and no score",
               "four kinds of finding", "has asked heata", "has written to Codema",
               "Permission requests are out", "has not had an answer",
               "capability proof", "build asserts", "fails closed"):
    must(phrase.lower() not in visible.lower(),
         "implementation language absent from homeowner copy: %r" % phrase)

# 2 . the seven positions lead, and every demoted fact survived
must(html.count('class="pos-eq"') == 7, "seven leading position ideas")
must(html.count('<div class="pos">') == 7, "seven position blocks")
must(html.count('<details class="faq-item is-inline">') == 7,
     "one detail drawer per position")
lost = [f for f in MUST_SURVIVE if f not in html]
must(not lost, "every demoted fact survived (%s)"
     % ("lost: " + "; ".join(lost[:6]) if lost else "none lost"))

# 3 . the ground-source revelation is back, and bounded
must("The ground can do more than heat a house." in html,
     "ground-source revelation restored")
must("Some systems can also use that same ground connection for cooling." in html,
     "cooling returns as a concept, conditioned")
must("depends on the system, the ground\n          conditions and the design" in html,
     "cooling is conditioned on system, ground and design")
must("has not established, from a\n            first-party Irish source" in html,
     "the Irish cooling limitation is in the evidence layer")
for overclaim in ("will provide cooling", "gives free cooling",
                  "provides passive cooling", "free cooling in summer"):
    must(overclaim.lower() not in html.lower(),
         "no cooling overclaim: %r" % overclaim)

# 4 . no generalisation from Tandem to all Irish operators
for g in ("any Irish operator", "no Irish operator", "Irish operators&rsquo;",
          "not connected to an Irish house by anyone"):
    must(g.lower() not in html.lower(), "no operator generalisation: %r" % g)
must("Tandem has confirmed that individual homes are not part of its current "
     "pipeline" in html.replace("\n", " ").replace("  ", " "),
     "the bounded Tandem formulation is present")

# 5 . the image notes are quiet, and there are no loud rights blocks left
must('class="rights"' not in html, "no operational rights block remains")
must(html.count('class="imgnote"') == 4, "four quiet image notes")
# whitespace-normalised: the wind note wraps the same sentence across lines
flat = re.sub(r"\s+", " ", html)
must(flat.count("Real installation photography will be added when publication "
                "rights are confirmed.") == 4,
     "each image note carries the one editorial sentence")

# 6 . the story and the flagship survive untouched
for beat in ("bolted to the hot water cylinder",            # compute abroad
             "already heats buildings in Tallaght",          # Tallaght
             "not what it does today",                       # Tandem, bounded
             "The energy anatomy of your property",          # the anatomy
             "do some of the work of a data centre"):        # the flagship
    must(beat in html, "story beat preserved: %r" % beat)
must(html.count('class="seam reveal"') == 1
     and html.index('class="seam reveal"')
     < html.index("The energy anatomy of your property"),
     "the honesty break still precedes the energy anatomy")

# the battery boundary moved into the drawer and is still bounded
must(html.count("PN-DISC026-BATTERY-BOUNDARY-BEGIN") == 1
     and html.count("PN-DISC026-BATTERY-BOUNDARY-END") == 1,
     "the battery boundary markers survived the move into the drawer")
must("From 6 October 2026 SEAI is to pay a flat" in html,
     "the battery grant is still in announced form")

# NO EVIDENCE CLAIM WIDENED. The set of euro amounts must be IDENTICAL to the
# set before this pass -- an editorial pass that changes a figure is not one.
AMT = re.compile(r"&euro;(\d{1,3}(?:,\d{3})*)")
before_amts = set(AMT.findall(PAGE.read_text(encoding="utf-8")))
after_amts = set(AMT.findall(html))
must(before_amts == after_amts,
     "the set of euro figures is unchanged (%s -> %s)"
     % (sorted(before_amts), sorted(after_amts)))

# structure
must(html.count("<main") == html.count("</main>"), "main balanced")
must(html.count("<section") == html.count("</section>"), "section balanced")
must(html.count("<div") == html.count("</div>"), "div balanced")
must(html.count("<details") == html.count("</details>") == 8,
     "eight drawers: seven positions and the hero summary")
must(html.count("<svg") == html.count("</svg>") == 4, "four SVGs, unchanged count")
must(FIGURE in html, "the anatomy figure is byte-identical to the one lifted")

bad = [lab for ok, lab in checks if not ok]
print("DISC-026 EDITORIAL PASS")
print("=" * 74)
for ok, lab in checks:
    print("  %s  %s" % ("PASS" if ok else "FAIL", lab))
print("=" * 74)
if bad:
    print("REFUSED -- %d assertion(s) failed. Nothing written." % len(bad))
    sys.exit(2)

PAGE.write_text(html, encoding="utf-8")
print("WROTE %s (%d checks passed, %d -> %d bytes)"
      % (PAGE.name, len(checks), BEFORE_LEN, len(html)))
