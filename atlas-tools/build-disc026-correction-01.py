#!/usr/bin/env python3
"""
DISC-026 . FOUNDER VISUAL REVIEW . CORRECTION PASS 01
===========================================================================
Bounded visual and language correction from the founder's review of the frozen
candidate d9936e0c0c01. No new research. No change to the evidence base. No
commit, push or deploy.

  1  "Read those figures carefully." removed, with the smallest grammatical
     repair and no replacement instruction to the reader.
  2  CATEGORY LABELS ANSWER "WHAT IS THIS?". Geographic and story kickers
     become technology/concept categories in the existing small uppercase
     treatment. CATEGORY -> REVELATION -> STATUS.
  3  The mechanism line is rewritten to the founder's wording.
  4  The honesty seam is rewritten and simplified; the self-explanation goes,
     the limitation stays, the two unconditional findings are untouched.
  5  The Tandem introduction is shortened; the long headline becomes a short
     one and the detail moves into the supporting copy.
  6  VISUAL HIERARCHY. An explicit five-level scale is declared in the CSS and
     the page is made to obey it. Too many sentences carried near-hero
     authority: the spark and the closing line were each consuming most of a
     viewport, and every section headline was set at proof scale.
  7  THE DEVELOPMENT-SCALE DIAGRAM IS REPLACED by a finished editorial
     illustration -- a section through an energy centre, a heat main and a
     cluster of homes, in PlotNua's own linework. The "nothing to photograph"
     sentence goes; the caption carries the state.
  8  THE OTHER DRAWINGS ARE AUDITED AND REFINED. The heat mechanism becomes a
     compact strip. The energy anatomy is redrawn to a finished standard with
     numbered markers. A to-scale WIND ENVELOPE diagram is added, because the
     caption under the wind position claimed a scale drawing that did not
     exist -- that claim is corrected either way.

EVERY ANCHOR MUST MATCH EXACTLY ONCE or the build refuses with sys.exit(2)
and writes nothing. A second run refuses.

Run: python3 atlas-tools/build-disc026-correction-01.py
"""

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
BEFORE_LEN = len(html)


def die(msg):
    print("REFUSED: " + msg)
    sys.exit(2)


def anchored(text, old, new, expect=1, label=""):
    n = text.count(old)
    if n != expect:
        die("anchor %r matched %d time(s), expected %d -- nothing written"
            % (label or old[:62], n, expect))
    return text.replace(old, new)


# ===========================================================================
# 6 . THE TYPE SCALE, DECLARED. Five levels, in one place, so the next person
#     can see the intent rather than infer it from clamp values.
# ===========================================================================

CSS = """
  /* ==================================================================
     FOUNDER VISUAL REVIEW, CORRECTION 01 . THE TYPE SCALE, DECLARED.

     The review finding was that too many sentences carried near-hero
     authority. Five levels now, and nothing is allowed to sit between
     them:

       A  FLAGSHIP HERO        h1            32 -> 58px
       B  REVELATION / PROOF   h2.is-proof   26 -> 40px
          and the seam         .seam h2      26 -> 42px
          and the anatomy      .pos-eq       27 -> 48px
       C  SECTION HEADLINE     h2            23 -> 31px
       D  CATEGORY KICKER      .kicker       12px uppercase
       E  TRANSITION / SPARK   .spark p      18 -> 25px, compact

     WHAT CHANGED AND WHY. Every section h2 was set at 40px, which made
     the mechanism, the proof and the watching brief equally loud; B now
     belongs to the Tallaght proof alone, and C is a step below it. The
     spark was 40px italic inside 12vh of padding, so one sentence held
     most of a viewport; the closing line held nearly two-fifths of one
     in padding alone. Both are compressed without being weakened --
     they are still the quietest and most deliberate type on the page.

     The anatomy leading ideas are deliberately NOT reduced: the founder
     is reviewing them at this size.
     ================================================================== */

  /* C . the default section headline steps down from proof scale. */
  .article-section h2{ font-size:clamp(23px,2.6vw,31px); line-height:1.26;
    max-width:24ch; margin-bottom:22px; }
  /* B . and the proof keeps the authority it has earned. */
  .article-section h2.is-proof{ font-size:clamp(26px,3.4vw,40px);
    line-height:1.3; max-width:19ch; margin-bottom:26px; }

  /* E . the transition is compact. One sentence should not hold a screen. */
  .spark{ padding:7vh 7vw; }
  .spark p{ font-size:clamp(18px,1.9vw,25px); line-height:1.5; }
  .closing-line{ padding:11vh 7vw 10vh; }

  /* A compact figure, for a diagram that is a caption rather than a plate. */
  .fig-strip{ background:none; border:none; border-top:1px solid rgba(31,59,46,.22);
    border-radius:0; padding:22px 0 0; margin-top:30px; }
  .fig-strip svg{ display:block; width:100%; height:auto; }
  .fig-strip .anat-cap{ margin-top:14px; }

  @media (max-width:760px){
    .spark{ padding:6vh 20px; }
    .closing-line{ padding:9vh 20px 8vh; }
  }
"""

html = anchored(html, "\n</style>", "\n" + CSS + "\n</style>", 1, "CSS insert")


# ===========================================================================
# 1 . "READ THOSE FIGURES CAREFULLY."
#     The sentence it opened has to keep its subject, so "Every one of them"
#     becomes the opening clause. No replacement instruction.
# ===========================================================================

html = anchored(
    html,
    """<p style="margin-top:38px"><strong>Read those figures carefully.</strong> Every
      one of them is British or German, under those countries&rsquo; electricity
      prices and programmes.""",
    """<p style="margin-top:38px">Every one of those figures is British or German,
      under those countries&rsquo; electricity prices and programmes.""",
    1, "Read those figures carefully")


# ===========================================================================
# 2 . CATEGORY LABELS. CATEGORY -> REVELATION -> STATUS.
#     Only where a distinct technology or concept is first introduced. The
#     seam, S7's section kicker, the watching brief and the closing section
#     keep their story labels: the technology there is already explicit, or
#     there is no single technology to name.
# ===========================================================================

KICKERS = [
    ('<div class="kicker">The mechanism</div>',
     '<div class="kicker">Computing and heat</div>'),
    ('<div class="kicker">Somewhere else</div>',
     '<div class="kicker">Home compute &middot; useful heat</div>'),
    ('<div class="kicker">And in Ireland</div>',
     '<div class="kicker">Data centres &middot; useful heat</div>'),
    ('<div class="kicker">Who is building it here</div>',
     '<div class="kicker">Distributed compute &middot; Ireland</div>'),
]
for old, new in KICKERS:
    html = anchored(html, old, new, 1, "kicker " + old[-28:])

# The seven anatomy positions gain their technology beside their place. The
# place is the anatomy; the technology is the category. Both are wanted.
POS_LABELS = [
    ("1 &middot; Roof</span>",
     "1 &middot; Roof &middot; Solar energy</span>"),
    ("2 &middot; Utility room, garage or wall space</span>",
     "2 &middot; Utility room, garage or wall space &middot; Battery storage</span>"),
    ("3 &middot; The air beside the house</span>",
     "3 &middot; The air beside the house &middot; Air-source heat</span>"),
    ("4 &middot; The ground beneath the garden</span>",
     "4 &middot; The ground beneath the garden &middot; Ground-source energy</span>"),
    ("5 &middot; The open garden</span>",
     "5 &middot; The open garden &middot; Small wind</span>"),
    ("6 &middot; The driveway</span>",
     "6 &middot; The driveway &middot; EV energy</span>"),
    ("7 &middot; The grid connection</span>",
     "7 &middot; The grid connection &middot; Export and flexibility</span>"),
]
for old, new in POS_LABELS:
    html = anchored(html, old, new, 1, "position label " + old[:24])


# ===========================================================================
# 3 . THE MECHANISM LINE, to the founder's wording. The evidence beneath it
#     -- the CRU figures and the physics -- is untouched.
# ===========================================================================

html = anchored(
    html,
    "<h2>A computer cannot stop making heat. A house cannot stop needing it.</h2>",
    "<h2>Computers produce heat. Homes need heat.<br>What if one could help supply\n"
    "      the other?</h2>",
    1, "mechanism headline")


# ===========================================================================
# 4 . THE HONESTY SEAM. Rewritten, simplified, self-explanation removed. The
#     two unconditional findings are not touched.
# ===========================================================================

html = anchored(
    html,
    """    <h2>Nobody has published what a house would have to be.</h2>
    <p>Not the operators. Not the regulator. Not us. So nobody can tell you whether
      your property would qualify &mdash; because there is nothing yet to qualify
      against.</p>
    <p>PlotNua would rather say that plainly than invent a checklist and let you
      measure your house against it.</p>""",
    """    <h2>Nobody yet knows what a &ldquo;compute-ready&rdquo; home looks like.</h2>
    <p>There is no agreed standard for this yet. So today, nobody can reliably tell
      you whether an individual home would qualify.</p>""",
    1, "seam headline and supporting copy")


# ===========================================================================
# 5 . THE TANDEM INTRODUCTION. Short headline; the detail moves down into the
#     supporting copy, where it belongs. The bounded meaning is unchanged:
#     larger commercial and community sites today, homes not in the pipeline,
#     residential described by Tandem as something it believes is coming. No
#     partnership implied.
# ===========================================================================

html = anchored(
    html,
    """    <h2>An Irish company is building this now &mdash; and says individual homes are
      not what it does today.</h2>
    <span class="ev ev-emerging">Emerging &mdash; commercial and community sites</span>
    <p>We asked. The answer was more useful than a brochure would have been, because
      it included the part that rules your house out for the moment.</p>""",
    """    <h2>This is already being built in Ireland.</h2>
    <span class="ev ev-emerging">Emerging &mdash; commercial and community sites</span>
    <p>Tandem Compute is developing distributed AI infrastructure at larger
      commercial and community sites &mdash; places with a constant appetite for heat
      and the energy infrastructure already in the ground. We asked them about
      houses, and the answer was more useful than a brochure would have been.</p>""",
    1, "Tandem headline and lede")

html = anchored(
    html,
    """    <p style="margin-top:38px"><strong>And the part that matters most to you.</strong>
      Residential and garden scale is <strong>not part of the offering or the
      pipeline today</strong>. In the same breath they said they do think that is
      coming, pointing to very small distributed compute installations emerging in
      the United States.</p>
    <p>Tandem is not a PlotNua partner. This is one email exchange and a conversation
      being arranged, recorded here because what an operator says about its own
      limits is worth more than what anybody says about its promise.</p>""",
    """    <p style="margin-top:38px"><strong>Individual homes are not part of
      Tandem&rsquo;s current pipeline.</strong> In the same breath they said they do
      think that is coming, pointing to very small distributed compute installations
      emerging in the United States.</p>
    <p>Tandem is not a PlotNua partner. This is one email exchange and a conversation
      being arranged, recorded here because what an operator says about its own
      limits is worth more than what anybody says about its promise.</p>""",
    1, "Tandem residential paragraph")

# B . the Tallaght proof is the one headline that keeps proof scale.
html = anchored(
    html,
    "<h2>Waste heat from a data centre already heats buildings in Tallaght.</h2>",
    '<h2 class="is-proof">Waste heat from a data centre already heats buildings in\n'
    "      Tallaght.</h2>",
    1, "Tallaght proof headline")


# ===========================================================================
# 7 + 8 . THE DIAGRAMS.
# ===========================================================================

# ---- 8a . THE HEAT MECHANISM . REFINED to a compact strip. --------------
# The three-rectangle drawing duplicated what the new headline now says, and
# at 900x190 inside a bordered plate it had the visual weight of a proof. It
# becomes a single baseline with three glyphs: electricity in, computing,
# heat out -- and the one thing the headline cannot say, which is that a data
# centre pays twice.
OLD_STRIP_START = '    <div class="anat-fig" style="margin-top:34px">\n      <svg viewBox="0 0 900 190"'
OLD_STRIP_END = ("      <p class=\"anat-cap\">An illustration of the mechanism, drawn by "
                 "PlotNua. It is not\n        a photograph of an installation, and it is "
                 "not a design for one.</p>\n    </div>")
if html.count(OLD_STRIP_START) != 1 or html.count(OLD_STRIP_END) != 1:
    die("could not locate the heat-mechanism figure uniquely")
a = html.index(OLD_STRIP_START)
b = html.index(OLD_STRIP_END) + len(OLD_STRIP_END)

NEW_STRIP = r"""    <div class="fig-strip">
      <svg viewBox="0 0 900 132" role="img"
           aria-label="Electricity enters a computer, the computer does its work, and almost all of that electricity leaves again as heat. A data centre pays once for the electricity and again to throw the heat away.">
        <!-- one baseline, three stages, no boxes. Hairline rule, small glyphs,
             labels on the rule. A caption with pictures rather than a plate. -->
        <g fill="none" stroke="#1F3B2E">
          <path d="M28 72 H872" stroke-width="1" opacity=".30"/>
          <!-- stage ticks -->
          <path d="M28 66 V78 M300 66 V78 M572 66 V78 M872 66 V78"
                stroke-width="1" opacity=".30"/>
          <!-- chevrons along the rule -->
          <path d="M156 66 L166 72 L156 78" stroke-width="1.1" opacity=".5"/>
          <path d="M428 66 L438 72 L428 78" stroke-width="1.1" opacity=".5"/>
          <path d="M716 66 L726 72 L716 78" stroke-width="1.1" opacity=".5"/>
        </g>
        <!-- glyph 1 . electricity -->
        <g transform="translate(40,20)" fill="none" stroke="#1F3B2E" stroke-width="1.4">
          <path d="M14 0 L2 22 H11 L7 40 L21 16 H12 Z" stroke-linejoin="round"/>
        </g>
        <!-- glyph 2 . the processor -->
        <g transform="translate(306,20)" fill="none" stroke="#1F3B2E" stroke-width="1.4">
          <rect x="6" y="6" width="30" height="30" rx="1.5" fill="#8FAF8A" fill-opacity=".20"/>
          <rect x="15" y="15" width="12" height="12" rx="1"/>
          <path d="M6 14 H0 M6 21 H0 M6 28 H0 M36 14 H42 M36 21 H42 M36 28 H42
                   M14 6 V0 M21 6 V0 M28 6 V0 M14 36 V42 M21 36 V42 M28 36 V42"
                stroke-width="1"/>
        </g>
        <!-- glyph 3 . the cylinder, which is where the heat can go -->
        <g transform="translate(578,14)" fill="none" stroke="#1F3B2E" stroke-width="1.4">
          <path d="M4 12 C4 4 26 4 26 12 V46 C26 52 4 52 4 46 Z"
                fill="#8FAF8A" fill-opacity=".20"/>
          <path d="M4 12 C4 19 26 19 26 12" stroke-width="1" opacity=".6"/>
          <path d="M15 4 V0" stroke-width="1"/>
          <!-- rising heat -->
          <path d="M38 40 C44 34 38 30 44 24 M50 44 C56 38 50 34 56 28"
                stroke-width="1" opacity=".45"/>
        </g>
        <g font-family="Work Sans, sans-serif" fill="#1F3B2E" letter-spacing="1.6">
          <text x="28" y="100" font-size="8.5" fill="#4F6B4A">IN</text>
          <text x="28" y="116" font-size="10.5">ELECTRICITY</text>
          <text x="300" y="100" font-size="8.5" fill="#4F6B4A">WORK</text>
          <text x="300" y="116" font-size="10.5">COMPUTING</text>
          <text x="572" y="100" font-size="8.5" fill="#4F6B4A">OUT</text>
          <text x="572" y="116" font-size="10.5">HEAT, AND SOMEWHERE FOR IT TO GO</text>
        </g>
      </svg>
      <p class="anat-cap">A data centre pays twice: once for the electricity, and
        again to throw the heat away. Drawn by PlotNua &mdash; an illustration of the
        mechanism, not of an installation.</p>
    </div>"""

html = html[:a] + NEW_STRIP + html[b:]


# ---- 7 . THE DEVELOPMENT-SCALE MODEL . REPLACED. -----------------------
# A section, not a flowchart: an energy centre, a heat main in the ground, and
# a cluster of homes in elevation. Architectural rather than diagrammatic,
# which is what stops it reading as a wireframe placeholder.
OLD_MODEL_START = ('    <div class="anat-fig" style="margin-top:36px">\n'
                   '      <svg viewBox="0 0 900 200"')
OLD_MODEL_END = ("        photograph.</p>\n    </div>")
if html.count(OLD_MODEL_START) != 1 or html.count(OLD_MODEL_END) != 1:
    die("could not locate the development-model figure uniquely")
a = html.index(OLD_MODEL_START)
b = html.index(OLD_MODEL_END) + len(OLD_MODEL_END)

NEW_MODEL = r"""    <div class="anat-fig" style="margin-top:36px">
      <svg viewBox="0 0 900 420" role="img"
           aria-label="A section through a development-scale model: an energy centre housing compute and combined heat and power, a heat main running under the street, and four homes in a development taking heat from it.">
        <!-- GROUND. A single line with a shallow hatch band under it, so the
             buried main reads as buried rather than floating. -->
        <defs>
          <pattern id="d26soil" width="9" height="9" patternUnits="userSpaceOnUse"
                   patternTransform="rotate(38)">
            <path d="M0 0 V9" stroke="#1F3B2E" stroke-width=".6" opacity=".22"/>
          </pattern>
        </defs>
        <rect x="40" y="258" width="820" height="104" fill="url(#d26soil)"/>
        <path d="M40 258 H860" stroke="#1F3B2E" stroke-width="1.6" opacity=".7" fill="none"/>

        <!-- THE ENERGY CENTRE. A plain industrial volume: parapet, louvre
             band, flue. No glow, no server imagery. -->
        <g fill="none" stroke="#1F3B2E">
          <rect x="68" y="150" width="176" height="108" stroke-width="1.5"
                fill="#8FAF8A" fill-opacity=".13"/>
          <path d="M62 150 H250" stroke-width="2"/>
          <path d="M86 176 H150 M86 186 H150 M86 196 H150" stroke-width="1" opacity=".5"/>
          <rect x="176" y="172" width="50" height="62" stroke-width="1" opacity=".55"/>
          <path d="M188 184 H214 M188 196 H214 M188 208 H214" stroke-width="1" opacity=".4"/>
          <path d="M214 150 V124 H226 V150" stroke-width="1.3"/>
          <!-- the two services leaving the building -->
          <path d="M156 258 V300" stroke-width="1.2" opacity=".65"/>
          <path d="M170 258 V312" stroke-width="1.2" opacity=".45"/>
        </g>

        <!-- THE HEAT MAIN. Flow and return, as a pair, running under the
             street and rising into each home. -->
        <g fill="none" stroke="#1F3B2E">
          <path d="M156 300 H790" stroke-width="1.6" opacity=".75"/>
          <path d="M170 312 H776" stroke-width="1.2" opacity=".45"/>
          <!-- direction, stated once -->
          <path d="M470 294 L482 300 L470 306" stroke-width="1.1" opacity=".6"/>
        </g>

        <!-- FOUR HOMES, in elevation, with varied ridge heights so the row
             reads as houses rather than as repeated icons. Each takes a
             riser off the main. -->
        <g fill="none" stroke="#1F3B2E">
          <!-- house 1 -->
          <path d="M448 258 V202 L492 170 L536 202 V258" stroke-width="1.5"
                fill="#8FAF8A" fill-opacity=".10"/>
          <path d="M442 204 L492 168 L542 204" stroke-width="1.8"/>
          <rect x="466" y="222" width="20" height="36" stroke-width="1" opacity=".55"/>
          <path d="M492 300 V258" stroke-width="1.1" opacity=".6"/>
          <circle cx="492" cy="258" r="3" stroke-width="1" opacity=".7"/>
          <!-- house 2 -->
          <path d="M552 258 V212 L592 182 L632 212 V258" stroke-width="1.5"
                fill="#8FAF8A" fill-opacity=".10"/>
          <path d="M546 214 L592 180 L638 214" stroke-width="1.8"/>
          <rect x="570" y="228" width="18" height="30" stroke-width="1" opacity=".55"/>
          <path d="M592 300 V258" stroke-width="1.1" opacity=".6"/>
          <circle cx="592" cy="258" r="3" stroke-width="1" opacity=".7"/>
          <!-- house 3 -->
          <path d="M650 258 V198 L694 166 L738 198 V258" stroke-width="1.5"
                fill="#8FAF8A" fill-opacity=".10"/>
          <path d="M644 200 L694 164 L744 200" stroke-width="1.8"/>
          <rect x="668" y="218" width="20" height="40" stroke-width="1" opacity=".55"/>
          <path d="M694 300 V258" stroke-width="1.1" opacity=".6"/>
          <circle cx="694" cy="258" r="3" stroke-width="1" opacity=".7"/>
          <!-- house 4 -->
          <path d="M754 258 V208 L792 180 L830 208 V258" stroke-width="1.5"
                fill="#8FAF8A" fill-opacity=".10"/>
          <path d="M748 210 L792 178 L836 210" stroke-width="1.8"/>
          <rect x="770" y="226" width="18" height="32" stroke-width="1" opacity=".55"/>
          <path d="M792 300 V258" stroke-width="1.1" opacity=".6"/>
          <circle cx="792" cy="258" r="3" stroke-width="1" opacity=".7"/>
        </g>

        <!-- recovered heat, shown as three short rises off the plant, not as
             an arrow between two boxes -->
        <g fill="none" stroke="#4F6B4A" stroke-width="1.1" opacity=".55">
          <path d="M268 140 C276 130 268 124 276 114"/>
          <path d="M286 148 C294 138 286 132 294 122"/>
          <path d="M304 140 C312 130 304 124 312 114"/>
        </g>

        <g font-family="Work Sans, sans-serif" fill="#1F3B2E" letter-spacing="1.6">
          <text x="68" y="112" font-size="8.5" fill="#4F6B4A">ENERGY CENTRE</text>
          <text x="68" y="392" font-size="10.5">COMPUTE, WITH CHP WHERE THE</text>
          <text x="68" y="408" font-size="10.5">GAS INFRASTRUCTURE EXISTS</text>
          <text x="330" y="112" font-size="8.5" fill="#4F6B4A">RECOVERED HEAT</text>
          <text x="330" y="340" font-size="8.5" fill="#4F6B4A">HEAT MAIN, IN THE GROUND</text>
          <text x="448" y="140" font-size="8.5" fill="#4F6B4A">THE DEVELOPMENT</text>
          <text x="448" y="392" font-size="10.5">HOMES TAKING HEAT FROM</text>
          <text x="448" y="408" font-size="10.5">A SHARED NETWORK</text>
        </g>
      </svg>
      <p class="anat-cap">How a development-scale model could work. Illustration based
        on the model described by Tandem Compute. Centralised heating is a
        precondition of that model, not a detail.</p>
    </div>"""

html = html[:a] + NEW_MODEL + html[b:]


# ---- 8b . THE ENERGY ANATOMY . REFINED. -------------------------------
# Same composition, because the founder is reviewing it; finished to the same
# standard as the illustration above. Numbered markers instead of bare
# numerals, a real roof with eaves, a panel array rather than a thick line, a
# serpentine ground loop rather than three straight lines, louvres on the
# air-source unit, and a taller viewBox so nothing crowds the labels.
OLD_ANAT_FIG_START = '      <div class="anat-fig">\n        <svg viewBox="0 0 900 400"'
OLD_ANAT_FIG_END = ("          structure. Nothing here is a recommendation for any "
                    "particular house.</p>\n      </div>")
if html.count(OLD_ANAT_FIG_START) != 1 or html.count(OLD_ANAT_FIG_END) != 1:
    die("could not locate the energy-anatomy figure uniquely")
a = html.index(OLD_ANAT_FIG_START)
b = html.index(OLD_ANAT_FIG_END) + len(OLD_ANAT_FIG_END)

NEW_ANAT_FIG = r"""      <div class="anat-fig">
        <svg viewBox="0 0 900 470" role="img"
             aria-label="A cross-section of an ordinary house and its site with seven numbered positions: one, solar panels on the roof; two, a battery on the utility wall inside; three, an air-source unit beside the house; four, a ground loop beneath the garden; five, a small turbine in the open garden; six, a charger on the driveway; seven, the grid connection at the boundary.">
          <defs>
            <pattern id="d26ground" width="9" height="9" patternUnits="userSpaceOnUse"
                     patternTransform="rotate(38)">
              <path d="M0 0 V9" stroke="#1F3B2E" stroke-width=".6" opacity=".20"/>
            </pattern>
          </defs>

          <!-- GROUND -->
          <rect x="20" y="322" width="860" height="86" fill="url(#d26ground)"/>
          <path d="M20 322 H880" stroke="#1F3B2E" stroke-width="1.6" opacity=".7" fill="none"/>

          <!-- THE HOUSE. Pitched roof with eaves, a chimney, openings. -->
          <g fill="none" stroke="#1F3B2E">
            <path d="M296 322 V200 L408 124 L520 200 V322 Z" stroke-width="1.5"
                  fill="#8FAF8A" fill-opacity=".10"/>
            <path d="M286 203 L408 120 L530 203" stroke-width="2"/>
            <path d="M462 168 V132 H478 V180" stroke-width="1.3"/>
            <rect x="322" y="236" width="30" height="34" stroke-width="1" opacity=".5"/>
            <rect x="462" y="236" width="30" height="34" stroke-width="1" opacity=".5"/>
            <rect x="392" y="266" width="32" height="56" stroke-width="1" opacity=".5"/>
            <!-- 1 . PANEL ARRAY on the right roof plane, as a parallelogram
                 with module divisions, sitting proud of the tiles -->
            <path d="M420 146 L512 208 L500 216 L408 154 Z" stroke-width="1.4"
                  fill="#8FAF8A" fill-opacity=".30"/>
            <path d="M443 162 L431 170 M466 177 L454 185 M489 192 L477 200"
                  stroke-width=".9" opacity=".6"/>
            <!-- 2 . BATTERY, wall-mounted inside, with its bracket -->
            <path d="M318 196 V322" stroke-width="1" opacity=".35"/>
            <rect x="326" y="212" width="46" height="66" stroke-width="1.4"
                  fill="#8FAF8A" fill-opacity=".22"/>
            <path d="M334 222 H364 M334 232 H364" stroke-width=".9" opacity=".5"/>
            <circle cx="349" cy="258" r="6" stroke-width="1" opacity=".55"/>
            <!-- 3 . AIR-SOURCE UNIT beside the house, louvres and fan -->
            <rect x="540" y="268" width="58" height="54" stroke-width="1.4"
                  fill="#8FAF8A" fill-opacity=".18"/>
            <circle cx="569" cy="295" r="16" stroke-width="1" opacity=".55"/>
            <path d="M569 295 L569 281 M569 295 L581 302 M569 295 L557 302"
                  stroke-width="1" opacity=".55"/>
            <path d="M546 276 H592 M546 316 H592" stroke-width=".9" opacity=".4"/>
            <!-- 4 . GROUND LOOP, a serpentine in a shallow trench -->
            <path d="M120 356 H250 Q262 356 262 368 Q262 380 250 380 H120
                     Q108 380 108 392 Q108 404 120 404 H250"
                  stroke-width="1.4" opacity=".75"/>
            <path d="M104 344 H266" stroke-width=".9" opacity=".35" stroke-dasharray="4 4"/>
            <!-- 5 . SMALL TURBINE in the open garden, three blades -->
            <path d="M96 322 V214" stroke-width="1.5"/>
            <circle cx="96" cy="208" r="5" stroke-width="1.4"
                    fill="#8FAF8A" fill-opacity=".35"/>
            <path d="M96 203 V168 M100 211 L131 228 M92 211 L61 228" stroke-width="1.4"/>
            <!-- 6 . DRIVEWAY and charger -->
            <path d="M636 322 H842" stroke-width="2.2" opacity=".28"/>
            <path d="M652 334 H826" stroke-width=".9" opacity=".3" stroke-dasharray="7 7"/>
            <rect x="648" y="276" width="24" height="46" stroke-width="1.4"
                  fill="#8FAF8A" fill-opacity=".20"/>
            <circle cx="660" cy="290" r="5" stroke-width="1" opacity=".55"/>
            <path d="M672 300 C690 300 694 310 706 310" stroke-width="1" opacity=".5"/>
            <!-- 7 . GRID CONNECTION at the boundary -->
            <path d="M858 322 V196" stroke-width="1.5"/>
            <path d="M836 200 H880 M842 212 H874" stroke-width="1.2"/>
            <path d="M858 226 C800 226 760 232 700 232" stroke-width="1" opacity=".45"/>
            <path d="M700 232 C640 232 560 212 530 206" stroke-width="1" opacity=".45"
                  stroke-dasharray="5 5"/>
          </g>

          <!-- NUMBERED MARKERS. A circle reads as a key; a bare numeral reads
               as a leftover. -->
          <g font-family="Work Sans, sans-serif" font-size="9.5" font-weight="500"
             text-anchor="middle">
            <g fill="#8FAF8A" fill-opacity=".30" stroke="#1F3B2E" stroke-width="1">
              <circle cx="470" cy="150" r="10"/>
              <circle cx="300" cy="186" r="10"/>
              <circle cx="612" cy="258" r="10"/>
              <circle cx="90"  cy="418" r="10"/>
              <circle cx="40"  cy="208" r="10"/>
              <circle cx="640" cy="258" r="10" opacity="0"/>
              <circle cx="700" cy="268" r="10"/>
              <circle cx="858" cy="170" r="10"/>
            </g>
            <g fill="#1F3B2E">
              <text x="470" y="154">1</text>
              <text x="300" y="190">2</text>
              <text x="612" y="262">3</text>
              <text x="90"  y="422">4</text>
              <text x="40"  y="212">5</text>
              <text x="700" y="272">6</text>
              <text x="858" y="174">7</text>
            </g>
          </g>

          <g font-family="Work Sans, sans-serif" fill="#1F3B2E" letter-spacing="1.5"
             font-size="10">
            <text x="486" y="154">ROOF</text>
            <text x="190" y="190" text-anchor="end">UTILITY WALL</text>
            <text x="628" y="262">AIR</text>
            <text x="106" y="422">GROUND</text>
            <text x="56"  y="212">GARDEN</text>
            <text x="716" y="272">DRIVEWAY</text>
            <text x="842" y="174" text-anchor="end">GRID</text>
          </g>
          <g font-family="Work Sans, sans-serif" font-size="10" fill="#55605A">
            <text x="20" y="456">An ordinary house, in section. Not your house, and not a design for one.</text>
          </g>
        </svg>
        <p class="anat-cap">Seven positions, drawn by PlotNua. Which of them apply
          depends entirely on the property &mdash; its age, its boundaries, its
          orientation, whether it has off-street parking, whether it is a protected
          structure.</p>
      </div>"""

html = html[:a] + NEW_ANAT_FIG + html[b:]


# ---- 8c . THE WIND ENVELOPE . NEW, and a caption corrected. ------------
# The note under the wind position said "The diagram above is drawn to the
# rule's own scale". The diagram above is the anatomy section, which is not.
# That sentence was not true, so it goes -- and the drawing it described is
# built, because the envelope is the whole of this route's story and it is
# pure geometry, which is the one kind of illustration that can be checked
# rather than judged. 1 metre = 24 px. Ground at y = 400.
WIND_FIG = r"""        <div class="anat-fig" style="margin-top:26px">
          <svg viewBox="0 0 900 470" role="img"
               aria-label="The exempt envelope for a domestic wind turbine, drawn to scale at one metre to twenty-four pixels: thirteen metres total height, a six metre rotor, a three metre minimum clearance between the ground and the lowest blade, and a setback from the party boundary of the total height plus one metre, which is fourteen metres at the maximum size.">
            <defs>
              <pattern id="d26nogo" width="7" height="7" patternUnits="userSpaceOnUse"
                       patternTransform="rotate(45)">
                <path d="M0 0 V7" stroke="#1F3B2E" stroke-width=".7" opacity=".22"/>
              </pattern>
              <pattern id="d26turf" width="9" height="9" patternUnits="userSpaceOnUse"
                       patternTransform="rotate(38)">
                <path d="M0 0 V9" stroke="#1F3B2E" stroke-width=".6" opacity=".18"/>
              </pattern>
            </defs>

            <rect x="30" y="400" width="840" height="34" fill="url(#d26turf)"/>
            <path d="M30 400 H870" stroke="#1F3B2E" stroke-width="1.6" opacity=".7" fill="none"/>

            <!-- THE MAXIMUM ENVELOPE: 13 m, dashed. -->
            <rect x="196" y="88" width="208" height="312" fill="none"
                  stroke="#4F6B4A" stroke-width="1" stroke-dasharray="6 5" opacity=".65"/>

            <!-- THE 3 m FLOOR the blades may not enter. -->
            <rect x="196" y="328" width="208" height="72" fill="url(#d26nogo)"/>
            <path d="M196 328 H404" stroke="#1F3B2E" stroke-width="1"
                  stroke-dasharray="4 4" opacity=".5" fill="none"/>

            <!-- THE HOUSE, for scale: 7 m to the ridge. The turbine may not be
                 sited in front of the building, so it stands behind it. -->
            <g fill="none" stroke="#1F3B2E">
              <path d="M44 400 V286 L104 244 L164 286 V400 Z" stroke-width="1.4"
                    fill="#8FAF8A" fill-opacity=".10"/>
              <path d="M36 289 L104 241 L172 289" stroke-width="1.8"/>
              <rect x="92" y="330" width="26" height="70" stroke-width="1" opacity=".5"/>
            </g>

            <!-- THE TURBINE, at a compliant configuration: hub at 10 m, a 6 m
                 rotor, so the tip reaches exactly 13 m and the lowest blade
                 sits at 7 m, well clear of the 3 m floor. -->
            <g fill="none" stroke="#1F3B2E">
              <path d="M300 400 V160" stroke-width="1.8"/>
              <circle cx="300" cy="160" r="6" stroke-width="1.6"
                      fill="#8FAF8A" fill-opacity=".35"/>
              <path d="M300 154 V88 M305 164 L362 196 M295 164 L238 196" stroke-width="1.6"/>
              <circle cx="300" cy="160" r="72" stroke="#4F6B4A" stroke-width=".9"
                      stroke-dasharray="3 5" opacity=".5"/>
            </g>

            <!-- DIMENSIONS -->
            <g fill="none" stroke="#1F3B2E" stroke-width="1" opacity=".75">
              <!-- 13 m total height -->
              <path d="M176 88 V400 M170 88 H182 M170 400 H182"/>
              <!-- 6 m rotor -->
              <path d="M424 88 V232 M418 88 H430 M418 232 H430"/>
              <!-- 3 m clearance -->
              <path d="M424 328 V400 M418 328 H430 M418 400 H430"/>
              <!-- setback: 14 m, mast to boundary -->
              <path d="M300 432 H636 M300 426 V438 M636 426 V438"/>
            </g>

            <!-- THE PARTY BOUNDARY -->
            <g fill="none" stroke="#1F3B2E">
              <path d="M636 400 V336" stroke-width="1.4"/>
              <path d="M636 348 H700 M636 364 H700 M636 380 H700"
                    stroke-width="1" opacity=".45"/>
            </g>

            <g font-family="Work Sans, sans-serif" fill="#1F3B2E" letter-spacing="1.4"
               font-size="10">
              <text x="166" y="240" text-anchor="end">13 m TOTAL HEIGHT</text>
              <text x="440" y="164">6 m ROTOR</text>
              <text x="440" y="370">3 m MINIMUM CLEARANCE</text>
              <text x="440" y="386" font-size="8.5" fill="#55605A">BLADES MAY NOT ENTER THIS BAND</text>
              <text x="468" y="426" text-anchor="middle">14 m SETBACK</text>
              <text x="712" y="368">PARTY BOUNDARY</text>
            </g>
            <g font-family="Work Sans, sans-serif" font-size="10" fill="#55605A">
              <text x="30" y="462">Drawn to scale. 14 m is the total height plus one metre, at the maximum exempt size.</text>
            </g>
          </svg>
          <p class="anat-cap">The exempt envelope, drawn to scale. The turbine shown
            sits inside it: a 6 m rotor with its hub at 10 m reaches 13 m exactly, and
            its lowest blade stays well above the 3 m floor. The setback is measured
            from the mast to the nearest party boundary.</p>
        </div>
"""

html = anchored(
    html,
    """        <span class="imgnote">The diagram above is drawn to the rule&rsquo;s own
          scale. Real installation photography will be added when publication rights
          are confirmed.</span>""",
    WIND_FIG + """        <span class="imgnote">Real installation photography will be added when publication rights are confirmed.</span>""",
    1, "wind envelope figure and corrected note")


# ===========================================================================
# ASSERTIONS
# ===========================================================================

checks = []


def must(cond, label):
    checks.append((bool(cond), label))


# 1
must("Read those figures carefully" not in html,
     "'Read those figures carefully.' is gone")
must("Every one of those figures is British or German" in html,
     "the sentence keeps its subject and its meaning")
for instruction in ("Read carefully", "Note carefully", "Bear in mind that every"):
    must(instruction not in html, "no replacement reader instruction: %r" % instruction)

# 2
for cat in ("Computing and heat", "Home compute &middot; useful heat",
            "Data centres &middot; useful heat",
            "Distributed compute &middot; Ireland"):
    must('<div class="kicker">' + cat + "</div>" in html, "category label: %s" % cat)
for gone in ("The mechanism", "Somewhere else", "And in Ireland",
             "Who is building it here"):
    must('<div class="kicker">' + gone + "</div>" not in html,
         "story label retired: %s" % gone)
for keep in ("The honest part", "Today in Ireland", "What we&rsquo;re watching",
             "What PlotNua is doing about it"):
    must('class="kicker">' + keep + "<" in html,
         "non-technology label kept: %s" % keep)
for tech in ("Solar energy", "Battery storage", "Air-source heat",
             "Ground-source energy", "Small wind", "EV energy",
             "Export and flexibility"):
    must("&middot; " + tech + "</span>" in html, "position category: %s" % tech)

# 3
must("Computers produce heat. Homes need heat." in html, "mechanism line rewritten")
must("What if one could help supply" in html, "mechanism question present")
must("A computer cannot stop making heat" not in html, "old mechanism line gone")
must("5% of the country&rsquo;s electricity in 2015" in html,
     "the CRU evidence under the mechanism is untouched")
must("31% by 2034" in html, "the CRU projection is untouched")

# 4
must("Nobody yet knows what a &ldquo;compute-ready&rdquo; home looks like." in html,
     "seam headline rewritten")
must("There is no agreed standard for this yet." in html, "seam copy simplified")
must("PlotNua would rather say that plainly" not in html,
     "the self-explanation is removed")
must("Nobody has published what a house would have to be" not in html,
     "old seam headline gone")
must("Distributed residential computing is not currently commercially" in html,
     "RCR finding 1 still verbatim")
must("no one can tell you whether a property is technically" in html,
     "RCR finding 2 still verbatim")

# 5
must("<h2>This is already being built in Ireland.</h2>" in html,
     "Tandem headline shortened")
must("An Irish company is building this now" not in html, "old Tandem headline gone")
must("Tandem Compute is developing distributed AI infrastructure at larger" in html,
     "Tandem explained in the supporting copy")
must("Individual homes are not part of\n      Tandem&rsquo;s current pipeline." in html,
     "the pipeline limit is stated, bounded to Tandem")
must("Tandem is not a PlotNua partner" in html, "no partnership implied")
must("suitable existing gas infrastructure" in html.replace("<em>", "").replace("</em>", ""),
     "the CHP precondition still travels with its claim")
must("centralised heating" in html.lower(),
     "the centralised-heating precondition still travels with its claim")

# 6
must('<h2 class="is-proof">' in html and html.count('class="is-proof"') == 1,
     "exactly one proof-scale headline, and it is Tallaght")
must("already heats buildings in\n      Tallaght" in html,
     "the proof headline is the Tallaght one")
must(".article-section h2{ font-size:clamp(23px,2.6vw,31px)" in html,
     "section headlines step down to level C")
must(".spark{ padding:7vh 7vw; }" in html, "the transition is compact")
must(".closing-line{ padding:11vh 7vw 10vh; }" in html, "the closing line is compact")
must(".pos-eq{ display:block;" in html and "48px" in html,
     "the anatomy leading ideas are NOT reduced")

# 7 + 8
must("There is no photograph here because there is nothing to" not in html,
     "the 'nothing to photograph' sentence is removed")
must("How a development-scale model could work. Illustration based" in html,
     "the required caption is present")
must("The diagram above is drawn to the rule&rsquo;s own" not in html,
     "the untrue scale claim under the wind position is corrected")
must(html.count("<svg") == html.count("</svg>") == 5,
     "five SVGs: hero annotation, heat strip, development model, anatomy, wind envelope")
must('viewBox="0 0 900 132"' in html, "the heat mechanism is a compact strip")
must('viewBox="0 0 900 420"' in html, "the development model is a full illustration")
must('viewBox="0 0 900 470"' in html and html.count('viewBox="0 0 900 470"') == 2,
     "the anatomy and the wind envelope are both full plates")
must("PowerPoint" not in html and "flowchart" not in html.lower(),
     "no flowchart language reached the page")
# the wind envelope must be arithmetically honest at 24px to the metre
must('d="M176 88 V400' in html, "13 m dimension spans 312px = 13 x 24")
must('d="M424 88 V232' in html, "6 m rotor dimension spans 144px = 6 x 24")
must('d="M424 328 V400' in html, "3 m clearance spans 72px = 3 x 24")
must('d="M300 432 H636' in html, "14 m setback spans 336px = 14 x 24")

# NOTHING WIDENED. The euro set and every governed figure must be identical.
AMT = re.compile(r"&euro;(\d{1,3}(?:,\d{3})*)")
must(set(AMT.findall(ORIGINAL)) == set(AMT.findall(html)),
     "the set of euro figures is unchanged")
for fig in ("13&nbsp;m", "6&nbsp;m rotor", "3&nbsp;m clearance", "43&nbsp;dB(A)",
            "2.3", "5&nbsp;kWh", "two million smart meters", "50&nbsp;m",
            "22%", "31%", "1,400+", "133", "100% covered by waste heat",
            "4.25&nbsp;kWh", "62% less gas"):
    must(fig in html, "governed figure untouched: %s" % fig)
must("From 6 October 2026 SEAI is to pay a flat" in html,
     "the battery boundary is untouched")
must(html.count("PN-DISC026-BATTERY-BOUNDARY-BEGIN") == 1,
     "the battery boundary markers are untouched")

# structure
must(html.count("<main") == html.count("</main>"), "main balanced")
must(html.count("<section") == html.count("</section>"), "section balanced")
must(html.count("<div") == html.count("</div>"), "div balanced")
must(html.count("<details") == html.count("</details>") == 8, "eight drawers")
must(html.count('class="pos-eq"') == 7, "seven leading ideas")
must(html.count('class="imgnote"') == 4, "four quiet image notes")
must('class="rights"' not in html, "no operational rights block")

bad = [lab for ok, lab in checks if not ok]
print("DISC-026 VISUAL REVIEW . CORRECTION 01")
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
