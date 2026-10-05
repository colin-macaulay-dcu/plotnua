#!/usr/bin/env python3
"""
DISC-026 — GOVERNED REBUILD OF THE DISCOVERY NARRATIVE PAGE.
===========================================================================
Rebuilds discovery-house-as-power-station.html to the founder-approved nine
section storyboard of 4 October 2026, with the three founder corrections:

  CORRECTION 1  S7 is THE ENERGY ANATOMY OF THE PROPERTY -- roof, utility /
                wall space, air, ground, garden, driveway, grid connection.
  CORRECTION 2  The sentence "the envelope places the rotor in the worst air
                on most sites" is REMOVED. The evidence does not establish it
                to the required standard. This builder asserts its absence.
  CORRECTION 3  The ending returns to the flagship revelation.

WHY A BOUNDED BUILDER AND NOT AN EDIT. Every anchor below must match EXACTLY
ONCE or the build refuses with sys.exit(2) and writes nothing. A second run
also refuses, because the page it is handed no longer contains the anchors it
needs. That is the point: a builder that can run twice can half-run once.

WHAT IT MUST NOT TOUCH, and each is asserted after the write:
  * the hero asset fec77c3f0bae107a.jpg and its POTENTIAL-ASSET alt text --
    atlas-tools/prove-discovery-library-capability.py drives the real page and
    needs that marker present to prove the Library guard still refuses a
    before-plate.
  * the asset ce9da2e51c945693.jpg -- the governed Library card image for this
    Discovery. prove-discovery-library-images.mjs (P4) requires it to appear on
    this page, with no potential-asset marker in its page-side alt.
  * the shell: Cookiebot, gtag, canonical, favicons, brand mark, floating
    Back, Related Discoveries, footer, reveal observer.

THE BATTERY DATE BOUNDARY. The SEAI battery grant is stated in ANNOUNCED form,
naming 6 October 2026 on its face, between the markers
PN-DISC026-BATTERY-BOUNDARY-BEGIN / -END. That sentence is true before the
date and true after it, so nothing published here asserts a scheme is open
before it is. Converting it to the present tense on or after 6 October is a
single anchored edit inside those markers and is NOT part of this build.

NO REMOTE IMAGERY. Every image reference is a relative PlotNua asset, so the
image-rights gate's remote scope is untouched. The five permission requests
(Codema, heata, SEAI, Precision Heating, Heverin) are all UNKNOWN; UNKNOWN
fails closed, so not one real photograph appears. The positions that want one
are built as data (PHOTO_SLOTS) and render nothing until a grant exists.

Run: python3 atlas-tools/build-disc026-discovery-rebuild.py
"""

import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
PAGE = ROOT / "discovery-house-as-power-station.html"


def die(msg):
    print("REFUSED: " + msg)
    sys.exit(2)


if not PAGE.exists():
    die("discovery-house-as-power-station.html is not in the tree")

html = PAGE.read_text(encoding="utf-8")


def anchored(text, old, new, expect=1, label=""):
    """Replace OLD with NEW, refusing unless OLD occurs exactly EXPECT times."""
    n = text.count(old)
    if n != expect:
        die("anchor %r matched %d time(s), expected %d -- %s"
            % (label or old[:58], n, expect, "nothing written"))
    return text.replace(old, new)


# ---------------------------------------------------------------------------
# 1 . HEAD METADATA. The old description sells solar. The Discovery is not
#     about solar; solar is one position on the property.
# ---------------------------------------------------------------------------

OLD_DESC = ('<meta name="description" content="Most houses only use electricity. '
            'A growing number of Irish homes now make some of their own, and are '
            'paid for what they do not use. What an Irish home can do today, and '
            'what is still years away.">')
NEW_DESC = ('<meta name="description" content="Computing cannot stop making heat, '
            'and a house cannot stop needing it. What is already happening '
            'elsewhere, what is already happening in Tallaght, and what an Irish '
            'property can actually do today.">')
html = anchored(html, OLD_DESC, NEW_DESC, 1, "meta description")

OLD_OG = '<meta property="og:description" content="What if your home could help power the future?">'
NEW_OG = ('<meta property="og:description" content="What if your house could one day '
          'do some of the work of a data centre &mdash; and use the heat it creates?">')
html = anchored(html, OLD_OG, NEW_OG, 1, "og:description")

OLD_TW = '<meta name="twitter:description" content="What if your home could help power the future?">'
NEW_TW = ('<meta name="twitter:description" content="What if your house could one day '
          'do some of the work of a data centre &mdash; and use the heat it creates?">')
html = anchored(html, OLD_TW, NEW_TW, 1, "twitter:description")


# ---------------------------------------------------------------------------
# 2 . CSS. Five new components, tokens only, no new font and no new colour.
#     Everything else on the page is reused as it stands.
# ---------------------------------------------------------------------------

CSS = """
  /* ==================================================================
     DISC-026 REBUILD, 4 October 2026. Five components, built on the
     tokens this page already defines. No new colour, no new font, no
     third-party asset.

     .ev      evidence state. THREE values and deliberately no fourth:
              TODAY / EMERGING / FUTURE. Weight falls as certainty
              falls -- solid, dashed, dotted -- so the boundary is
              legible before the words are read.
     .seam    S6, the honesty break. The one dark full-bleed band on
              the page. Everything above it is somewhere else or
              someone else's; everything below it is available here.
     .anat    S7, the energy anatomy of the property.
     .chain   S9, generation through to the flagship.
     .rights  a reserved photograph position, stated honestly. UNKNOWN
              fails closed, so the position says so rather than being
              filled with a render.
     ================================================================== */

  .ev{ display:inline-block; font-family:'Work Sans',sans-serif;
    font-size:9px; font-weight:500; letter-spacing:.2em;
    text-transform:uppercase; padding:4px 10px 3px; border-radius:2px;
    margin:0 0 14px; border:1px solid rgba(31,59,46,.42);
    color:var(--ink); background:rgba(31,59,46,.07); }
  .ev-emerging{ background:none; border-style:dashed;
    border-color:rgba(31,59,46,.34); color:var(--soft); }
  .ev-future{ background:none; border-style:dotted;
    border-color:rgba(31,59,46,.26); color:var(--soft); }

  /* the band. Full-bleed, so it is set outside .article. */
  .seam{ margin:0; padding:clamp(66px,9vw,118px) 24px;
    background:var(--ink); color:var(--cream); }
  .seam-inner{ max-width:740px; margin:0 auto; }
  .seam .kicker{ display:block; font-family:'Work Sans',sans-serif;
    font-size:9.5px; font-weight:500; letter-spacing:.24em;
    text-transform:uppercase; color:var(--brand-sage); margin:0 0 20px; }
  .seam h2{ font-family:'Fraunces',Georgia,serif; font-weight:400;
    font-size:clamp(26px,3.6vw,42px); line-height:1.16;
    letter-spacing:-.018em; color:var(--brand-ivory); margin:0 0 26px; }
  .seam p{ font-family:'Work Sans',sans-serif; font-size:16px;
    line-height:1.8; margin:0 0 18px; color:rgba(242,239,230,.82);
    max-width:60ch; }
  .seam blockquote{ margin:30px 0 0; padding:22px 26px;
    border-left:2px solid var(--brand-sage);
    background:rgba(255,255,255,.05);
    font-family:'Fraunces',Georgia,serif; font-weight:400; font-size:17px;
    line-height:1.56; color:var(--brand-ivory); }
  .seam blockquote + blockquote{ margin-top:14px; }

  /* the anatomy: one figure, then one block per position. */
  .anat{ margin:38px 0 0; }
  .anat-fig{ background:var(--cream); border:1px solid rgba(31,59,46,.13);
    border-top:2px solid rgba(31,59,46,.42); border-radius:2px;
    padding:28px 26px 20px; }
  .anat-fig svg{ display:block; width:100%; height:auto; }
  .anat-cap{ font-family:'Work Sans',sans-serif; font-size:12px;
    line-height:1.68; color:var(--soft); margin:18px 0 0; max-width:66ch; }
  .pos{ margin:40px 0 0; padding:28px 0 0;
    border-top:1px solid rgba(31,59,46,.20); }
  .pos-where{ display:block; font-family:'Work Sans',sans-serif;
    font-size:9.5px; font-weight:500; letter-spacing:.22em;
    text-transform:uppercase; color:var(--accent); margin:0 0 10px; }
  .pos h3{ font-family:'Fraunces',Georgia,serif; font-weight:500;
    font-size:clamp(19px,2.1vw,24px); line-height:1.26; margin:0 0 14px; }
  .pos p{ font-family:'Work Sans',sans-serif; font-size:15px;
    line-height:1.78; margin:0 0 14px; max-width:62ch; color:var(--ink); }
  .pos-facts{ list-style:none; margin:18px 0 0; padding:0; display:grid;
    grid-template-columns:repeat(auto-fit,minmax(208px,1fr)); gap:1px;
    background:rgba(31,59,46,.13); border:1px solid rgba(31,59,46,.13);
    border-radius:2px; }
  .pos-facts > li{ margin:0; background:var(--paper);
    padding:17px 19px 19px; }
  /* the open question, where there is one. Quieter than a fact and
     visibly not one -- it is what PlotNua has NOT established. */
  .pos-open{ margin:18px 0 0; padding:17px 19px;
    background:rgba(31,59,46,.045);
    border-left:2px solid rgba(31,59,46,.30);
    font-family:'Work Sans',sans-serif; font-size:13.5px; line-height:1.72;
    color:var(--soft); max-width:66ch; }
  .pos-open strong{ color:var(--ink); font-weight:500; }

  .chain{ list-style:none; margin:34px 0 0; padding:0; }
  .chain > li{ margin:0; padding:18px 0; display:grid;
    grid-template-columns:30px 1fr; gap:16px; align-items:baseline;
    border-top:1px solid rgba(31,59,46,.12); }
  .chain > li:first-child{ border-top:2px solid rgba(31,59,46,.42); }
  .chain-n{ font-family:'Work Sans',sans-serif; font-size:10px;
    font-weight:500; letter-spacing:.12em; color:var(--accent); }
  .chain-t{ font-family:'Fraunces',Georgia,serif; font-weight:500;
    font-size:16px; line-height:1.4; color:var(--ink); }
  .chain-t span{ display:block; font-family:'Work Sans',sans-serif;
    font-size:12.5px; line-height:1.7; color:var(--soft); margin-top:6px; }

  .rights{ margin:26px 0 0; padding:15px 17px;
    border:1px dashed rgba(31,59,46,.30); border-radius:2px;
    font-family:'Work Sans',sans-serif; font-size:12px; line-height:1.72;
    color:var(--soft); max-width:70ch; }
  .rights b{ font-weight:500; color:var(--ink); }

  @media (max-width:760px){
    .seam{ padding:56px 20px; }
    .anat-fig{ padding:20px 16px 14px; }
    .pos-facts{ grid-template-columns:1fr; }
    .chain > li{ grid-template-columns:24px 1fr; gap:12px; }
  }
"""

STYLE_CLOSE = "\n</style>"
html = anchored(html, STYLE_CLOSE, "\n" + CSS + STYLE_CLOSE, 1, "CSS insert")


# ---------------------------------------------------------------------------
# 3 . HERO COPY. The flagship becomes the subtitle. The hero IMAGE and its
#     alt text are untouched -- see the module docstring.
# ---------------------------------------------------------------------------

OLD_HERO = """    <p class="subtitle">What if your home could help power the future?</p>
    <p class="intro">Your home already uses energy. In the future, it could do something much more unexpected with it.</p>"""
NEW_HERO = """    <p class="subtitle">What if your house could one day do some of the work of a
      data centre &mdash; and use the heat it creates?</p>
    <p class="intro">A house is somewhere electricity arrives. Computing is starting to
      move the other way &mdash; and computing cannot stop making heat.</p>"""
html = anchored(html, OLD_HERO, NEW_HERO, 1, "hero subtitle and intro")


# ---------------------------------------------------------------------------
# 4 . THE BODY. Everything between the hero and Related Discoveries is
#     replaced. Start and end anchors are both asserted unique.
# ---------------------------------------------------------------------------

START = """<main class="article">

  <!-- ============================================================
       THE DISCOVERY."""
END = ("<p>What PlotNua is watching for is the model that connects those "
       "pieces to computing.</p>\n</section>")

if html.count(START) != 1:
    die("the body START anchor matched %d times, expected 1" % html.count(START))
if html.count(END) != 1:
    die("the body END anchor matched %d times, expected 1" % html.count(END))

i = html.index(START)
j = html.index(END) + len(END)
if j <= i:
    die("the body anchors are in the wrong order; the page is not what this "
        "builder was written against")

BODY = r"""<main class="article">

  <!-- ====================================================================
       S2 . WHY A HOUSE AT ALL. One mechanism, before any company is named.
       The physics needs no citation. The SCALE claim does, and it is Irish
       and first-party: CRU, 12 December 2025.
       ==================================================================== -->
  <section class="article-section reveal">
    <div class="kicker">The mechanism</div>
    <h2>A computer cannot stop making heat. A house cannot stop needing it.</h2>
    <span class="ev">Today &mdash; the physics</span>
    <p>Almost all the electricity a computer draws leaves it as heat. A data centre
      spends more money getting rid of that heat. Your house spends money making it.
      Those are the same thing, pointing in opposite directions.</p>
    <p>In Ireland this stopped being a curiosity some time ago. Data centres took
      <strong>5% of the country&rsquo;s electricity in 2015</strong>. By
      <strong>2024 it was 22%</strong>, and the Commission for Regulation of
      Utilities projects <strong>31% by 2034</strong>.</p>
    <p>Put the computer where the heat is wanted, and the waste stops being waste.
      That is the whole idea. Everything below is about how close it actually is.</p>

    <!-- THE HEAT PATH. A diagram, not a photograph: it describes a mechanism
         and makes no claim that any particular installation exists. Drawn by
         PlotNua, so it carries no rights question. -->
    <div class="anat-fig" style="margin-top:34px">
      <svg viewBox="0 0 900 190" role="img"
           aria-label="Electricity enters a computer; almost all of it leaves as heat; that heat warms water in a cylinder, which heats the house.">
        <g fill="none" stroke="#1F3B2E" stroke-width="1.2">
          <rect x="22" y="58" width="150" height="74" rx="2" opacity=".55"/>
          <rect x="300" y="58" width="150" height="74" rx="2" opacity=".55"/>
          <rect x="578" y="58" width="150" height="74" rx="2" opacity=".55"/>
          <path d="M180 95 H292" opacity=".5"/>
          <path d="M281 89 L292 95 L281 101" opacity=".5"/>
          <path d="M458 95 H570" opacity=".5"/>
          <path d="M559 89 L570 95 L559 101" opacity=".5"/>
          <path d="M736 95 H864" opacity=".5"/>
          <path d="M853 89 L864 95 L853 101" opacity=".5"/>
        </g>
        <g font-family="Work Sans, sans-serif" font-size="10.5" fill="#1F3B2E"
           letter-spacing="1.6">
          <text x="40" y="88" font-size="8.5" fill="#4F6B4A">INPUT</text>
          <text x="40" y="108">ELECTRICITY</text>
          <text x="318" y="88" font-size="8.5" fill="#4F6B4A">WORK</text>
          <text x="318" y="108">COMPUTING</text>
          <text x="596" y="88" font-size="8.5" fill="#4F6B4A">OUTPUT</text>
          <text x="596" y="108">HEAT</text>
          <text x="754" y="92" font-size="8.5" fill="#4F6B4A">WHERE IT CAN GO</text>
          <text x="754" y="110" font-size="10.5">HOT WATER,</text>
          <text x="754" y="126" font-size="10.5">HEATING</text>
        </g>
        <g font-family="Work Sans, sans-serif" font-size="10" fill="#55605A">
          <text x="22" y="166">A data centre pays twice: once for the electricity, again to throw the heat away.</text>
        </g>
      </svg>
      <p class="anat-cap">An illustration of the mechanism, drawn by PlotNua. It is not
        a photograph of an installation, and it is not a design for one.</p>
    </div>
  </section>
</main>

<section class="spark reveal">
  <p>Not here yet. But not hypothetical either.</p>
</section>

<main class="article">

  <!-- ====================================================================
       S3 . IT IS ALREADY HAPPENING SOMEWHERE. The section that makes the
       Discovery credible, so it is specific, named and dated.

       NON-NEGOTIABLE, per the storyboard: every figure here is UK or German,
       under those countries' prices and programmes, and what the household
       receives in every operating case is HEAT. No "earn". No "could be paid".
       ==================================================================== -->
  <section class="article-section reveal">
    <div class="kicker">Somewhere else</div>
    <h2>There are houses today with a computer bolted to the hot water cylinder.</h2>
    <span class="ev ev-emerging">Emerging &mdash; outside Ireland</span>
    <p>Not a prototype in a lab. Occupied homes, with a submeter on the wall and a
      box on the cylinder. The household gets the hot water.</p>

    <div class="dq-adv">
      <span class="dq-cat dq-adv-cat">Operating now, outside Ireland</span>
      <ul class="dq-adv-cols is-four">
        <li>
          <span class="dq-adv-label">Britain &middot; in homes</span>
          <span class="dq-fact">A compute unit clamped to a domestic hot water
            cylinder through a patented thermal bridge. A billing-accredited
            submeter is fitted, and the household is credited for the electricity
            the unit uses.</span>
          <span class="dq-note">heata (Bit Warmer Ltd). The company&rsquo;s own
            modelling is 4.25&nbsp;kWh of hot water a day, up to
            &pound;340 a year. It needs a cylinder of roughly
            425&ndash;450&nbsp;mm diameter with clearance around it. British Gas
            ran a trial in employees&rsquo; homes.</span>
        </li>
        <li>
          <span class="dq-adv-label">Britain &middot; in homes</span>
          <span class="dq-fact">A household unit where the company pays for the
            electricity and sells the computing, and the heat stays in the
            house.</span>
          <span class="dq-note">Thermify HeatHub, deployed through the SHIELD
            trial with UK Power Networks. A second, independent household-scale
            precedent &mdash; which matters more than either one alone.</span>
        </li>
        <li>
          <span class="dq-adv-label">Britain &middot; building scale</span>
          <span class="dq-fact">An immersion-cooled &ldquo;digital boiler&rdquo;
            installed at a building with constant heat demand, displacing the gas
            that used to make that heat.</span>
          <span class="dq-note">Deep Green. At Exmouth Leisure Centre the reported
            result was 62% less gas for the pool and over &pound;20,000 a year
            saved. Blocks of flats are named as a target building type.</span>
        </li>
        <li>
          <span class="dq-adv-label">Germany &middot; specified</span>
          <span class="dq-fact">A household unit specified at 500&nbsp;W, desktop
            sized, silent, sitting behind the meter.</span>
          <span class="dq-note">CYANIS AI, Hamburg. The architecture is published;
            the household layer is not an open programme. It is here for one
            reason &mdash; it sets the physical scale of the idea.</span>
        </li>
      </ul>
    </div>

    <p style="margin-top:38px"><strong>Read those figures carefully.</strong> Every
      one of them is British or German, under those countries&rsquo; electricity
      prices and programmes. None of it is open to an Irish homeowner. And in every
      case that is actually operating, what the household receives is
      <strong>heat</strong> &mdash; not income.</p>

    <div class="rights">
      <b>A photograph belongs here and there isn&rsquo;t one yet.</b> The useful
      image is a compute unit on a real domestic cylinder, which would bound this
      idea honestly in a single frame. PlotNua has asked heata for permission and
      has not had an answer. Until permission is given, this position stays empty:
      we will not illustrate a real installation with a picture we generated.
    </div>
  </section>

  <!-- ====================================================================
       S4 . AND IT IS ALREADY HAPPENING IN IRELAND. The strongest Irish
       evidence on the page, and the most easily over-read -- so the
       limitation is in the same surface, not in a footnote.

       The 133 apartments are in the scheme's own FORWARD terms. Codema has
       not confirmed the connection is complete, so the present tense is not
       available to us. The founder's rule: if unconfirmed, forward terms.
       ==================================================================== -->
  <section class="article-section reveal">
    <div class="kicker">And in Ireland</div>
    <h2>Waste heat from a data centre already heats buildings in Tallaght.</h2>
    <span class="ev">Today &mdash; operating since 2023</span>
    <p>This is the part most people in Ireland have not heard. It is not a trial, it
      is not a pilot, and it has been running for three years.</p>

    <div class="dq-opp">
      <div class="dq-earn">
        <span class="dq-cat">The Tallaght District Heating Scheme</span>
        <p class="dq-earn-lead">Ireland&rsquo;s first large-scale district heating
          network of its kind. During normal operation, its heat demand is
          <strong>100% covered by waste heat from the neighbouring Amazon data
          centre</strong>.</p>
        <p class="dq-earn-caveat">Phase 1 has been operational since 2023, supplying
          South Dublin County Council&rsquo;s County Hall and library complex and
          buildings on the TU Dublin Tallaght campus. Operated by Heat Works,
          Ireland&rsquo;s first not-for-profit energy utility, wholly owned by South
          Dublin County Council.</p>
        <ul class="dq-figs">
          <li>
            <span class="dq-fig">1,400+</span>
            <span class="dq-src">Tonnes of CO&#8322; saved in 2025, on the
              scheme&rsquo;s own figures.</span>
          </li>
          <li>
            <span class="dq-fig">133</span>
            <span class="dq-src">Affordable apartments were set to connect as the
              scheme expanded in 2025. Whether that connection is complete is
              something PlotNua has asked Codema and has not yet been told.</span>
          </li>
        </ul>
      </div>
      <div class="dq-use">
        <span class="dq-cat">What it proves, and what it doesn&rsquo;t</span>
        <ul class="dq-rows">
          <li><span class="dq-fact"><strong>It proves the heat is real.</strong>
            Compute heat already reaches Irish buildings, including
            homes.</span></li>
          <li><span class="dq-fact"><strong>It arrives through a pipe.</strong> A
            heat network, built by a council-owned utility, fed by one
            utility-scale data centre.</span>
            <span class="dq-note">Nothing in it belongs to a household. There is no
              equipment on anybody&rsquo;s property.</span></li>
          <li><span class="dq-fact"><strong>It is not proof that a house can host
            computing.</strong> It is the opposite end of the same idea &mdash;
            district scale, delivered to buildings, not generated at
            them.</span></li>
        </ul>
      </div>
    </div>

    <div class="rights">
      <b>Photographs requested, not yet granted.</b> The images that would carry
      this &mdash; the energy centre, the campus buildings on the network, the
      apartments &mdash; belong to Codema, South Dublin County Council and Heat
      Works. PlotNua has written to Codema and is waiting. Irish proof has to be
      photographic or absent, so it is absent for now.
    </div>
  </section>

  <!-- ====================================================================
       S5 . WHERE IT PLAUSIBLY ARRIVES FIRST. Direct operator evidence,
       3 October 2026, one email exchange.

       HARD CONSTRAINTS. Tandem is NOT a PlotNua partner. Both preconditions
       travel with their claims -- "suitable existing gas infrastructure" for
       CHP, "with centralised heating" for the development model -- because
       Stage 1 showed both being dropped between the conversation and the
       note, and both materially narrow the claim.
       ==================================================================== -->
  <section class="article-section reveal">
    <div class="kicker">Who is building it here</div>
    <h2>An Irish company is building this now &mdash; and says individual homes are
      not what it does today.</h2>
    <span class="ev ev-emerging">Emerging &mdash; commercial and community sites</span>
    <p>We asked. The answer was more useful than a brochure would have been, because
      it included the part that rules your house out for the moment.</p>

    <div class="dq-adv">
      <span class="dq-cat dq-adv-cat">What the operator told us, October 2026</span>
      <ul class="dq-adv-cols is-four">
        <li>
          <span class="dq-adv-label">What they build</span>
          <span class="dq-fact">Distributed AI compute infrastructure at locations
            where the energy it produces can be put to productive use.</span>
          <span class="dq-note">Tandem Compute. A host site is judged on heat
            demand, existing energy infrastructure, power, fibre and physical
            space.</span>
        </li>
        <li>
          <span class="dq-adv-label">Where, today</span>
          <span class="dq-fact">Larger commercial and community sites &mdash; pools,
            leisure facilities, hotels, food production, industrial users.</span>
          <span class="dq-note">Places with a constant, year-round appetite for heat
            and the infrastructure already in the ground.</span>
        </li>
        <li>
          <span class="dq-adv-label">Increasingly examining</span>
          <span class="dq-fact">Compute combined with CHP &mdash;
            <em>where a site has suitable existing gas infrastructure</em>. The CHP
            makes electricity for the compute and useful heat, and the
            compute&rsquo;s own heat is recovered too.</span>
          <span class="dq-note">That condition is theirs, and it is load-bearing.
            Without the gas infrastructure, this route does not apply.</span>
        </li>
        <li>
          <span class="dq-adv-label">The nearer-term housing route</span>
          <span class="dq-fact">A housing or mixed-use development
            <em>with centralised heating</em>, hosting compute and CHP centrally and
            distributing the heat across the development.</span>
          <span class="dq-note">A development, not a house. The centralised-heating
            condition is theirs too.</span>
        </li>
      </ul>
    </div>

    <p style="margin-top:38px"><strong>And the part that matters most to you.</strong>
      Residential and garden scale is <strong>not part of the offering or the
      pipeline today</strong>. In the same breath they said they do think that is
      coming, pointing to very small distributed compute installations emerging in
      the United States.</p>
    <p>Tandem is not a PlotNua partner. This is one email exchange and a conversation
      being arranged, recorded here because what an operator says about its own
      limits is worth more than what anybody says about its promise.</p>

    <!-- A MODEL, labelled as one. No Irish development may be depicted as
         existing, because none does. -->
    <div class="anat-fig" style="margin-top:36px">
      <svg viewBox="0 0 900 200" role="img"
           aria-label="A model of the development-scale route: compute and combined heat and power at a central plant, feeding a heat network that serves the homes in a development.">
        <g fill="none" stroke="#1F3B2E" stroke-width="1.2">
          <rect x="22" y="40" width="190" height="110" rx="2" opacity=".55"/>
          <path d="M40 92 H194" opacity=".3"/>
          <path d="M220 95 H330" opacity=".5"/>
          <path d="M319 89 L330 95 L319 101" opacity=".5"/>
          <rect x="338" y="62" width="168" height="66" rx="2" opacity=".55"/>
          <path d="M514 95 H612" opacity=".5"/>
          <path d="M601 89 L612 95 L601 101" opacity=".5"/>
          <g opacity=".55">
            <path d="M636 128 V96 L660 76 L684 96 V128 Z"/>
            <path d="M700 128 V96 L724 76 L748 96 V128 Z"/>
            <path d="M764 128 V96 L788 76 L812 96 V128 Z"/>
          </g>
        </g>
        <g font-family="Work Sans, sans-serif" fill="#1F3B2E" letter-spacing="1.5">
          <text x="40" y="68" font-size="8.5" fill="#4F6B4A">CENTRAL PLANT</text>
          <text x="40" y="86" font-size="10.5">COMPUTE</text>
          <text x="40" y="116" font-size="10.5">CHP, WHERE THE GAS</text>
          <text x="40" y="132" font-size="10.5">INFRASTRUCTURE EXISTS</text>
          <text x="356" y="88" font-size="8.5" fill="#4F6B4A">DISTRIBUTION</text>
          <text x="356" y="108" font-size="10.5">HEAT NETWORK</text>
          <text x="636" y="62" font-size="8.5" fill="#4F6B4A">RECIPIENTS</text>
          <text x="636" y="150" font-size="10.5">HOMES IN THE DEVELOPMENT</text>
        </g>
        <g font-family="Work Sans, sans-serif" font-size="10" fill="#55605A">
          <text x="22" y="186">Centralised heating is a precondition, not a detail. Without it this route does not apply.</text>
        </g>
      </svg>
      <p class="anat-cap">A model of what the operator described, drawn by PlotNua.
        It is not a photograph of a built scheme, and no Irish development like this
        exists. There is no photograph here because there is nothing to
        photograph.</p>
    </div>
  </section>
</main>

<!-- ======================================================================
     S6 . THE HONESTY BREAK. The structural hinge of the whole Discovery.

     Everything above this band is somewhere else or someone else's.
     Everything below it is available in Ireland now. Without the break in
     this position, a reader arriving at the solar grant would reasonably
     assume the compute part is purchasable too.

     The two findings are carried VERBATIM from the Residential Compute
     Readiness work, where they are emitted unconditionally on every run.
     No image. An image here would soften a section whose entire value is
     that it is blunt.
     ====================================================================== -->
<section class="seam reveal">
  <div class="seam-inner">
    <span class="kicker">The honest part</span>
    <h2>Nobody has published what a house would have to be.</h2>
    <p>Not the operators. Not the regulator. Not us. So nobody can tell you whether
      your property would qualify &mdash; because there is nothing yet to qualify
      against.</p>
    <p>PlotNua would rather say that plainly than invent a checklist and let you
      measure your house against it.</p>
    <blockquote>Distributed residential computing is not currently commercially
      available through PlotNua in Ireland. PlotNua is investigating what would be
      required if this model enters the Irish market.</blockquote>
    <blockquote>Nobody has published the technical requirements a property would have
      to meet. Until they do, no one can tell you whether a property is technically
      compatible, and PlotNua will not pretend otherwise.</blockquote>
    <p style="margin-top:30px">Everything from here down is different. It is
      available in Ireland today, it is supported, and it is worth doing entirely on
      its own terms &mdash; whatever happens to the idea above.</p>
  </div>
</section>

<main class="article">

  <!-- ====================================================================
       S7 . THE ENERGY ANATOMY OF THE PROPERTY. Founder correction 1.

       Seven positions on an ordinary property: roof, utility or wall space,
       air, ground, garden, driveway, grid connection. Each one is a place,
       not a product -- the correction's whole point was that S7 must not
       become seven mini product guides.

       EVERY FIGURE HERE IS FIRST-PARTY. Per the governance rule of
       4 October 2026 (PLATFORM-EVIDENCE-GOVERNANCE.md 5a), no Irish grant
       or financial-support amount enters PlotNua from a secondary source.
       ==================================================================== -->
  <section class="article-section reveal">
    <div class="kicker">Today in Ireland</div>
    <h2>The energy anatomy of your property</h2>
    <span class="ev">Today &mdash; available in Ireland now</span>
    <p>Everything a house would have to be before it could ever do any of the above
      is already available here. Not as a package and not as a product &mdash; as
      seven separate places on an ordinary property, each of which can do something
      with energy rather than only consume it.</p>
    <p><strong>Doing all seven would not make your property compute-ready.</strong>
      Nothing can, because nobody has defined compute-ready. Each of these is worth
      doing for its own reasons, and that is the only promise on this page.</p>

    <div class="anat">
      <!-- THE ANATOMY FIGURE. Drawn by PlotNua. Seven positions, numbered to
           match the blocks below. A diagram, so it asserts nothing about any
           real property. -->
      <div class="anat-fig">
        <svg viewBox="0 0 900 400" role="img"
             aria-label="A cross-section of an ordinary house and its site, with seven numbered positions: the roof, the utility or wall space inside, the air beside the house, the ground beneath the garden, the open garden, the driveway, and the grid connection at the boundary.">
          <g fill="none" stroke="#1F3B2E" stroke-width="1.2">
            <!-- ground line -->
            <path d="M20 300 H880" opacity=".45"/>
            <!-- house -->
            <path d="M250 300 V176 L370 96 L490 176 V300 Z" opacity=".6"/>
            <!-- roof plane emphasis -->
            <path d="M262 170 L370 98 L478 170" stroke-width="2" opacity=".75"/>
            <!-- utility wall inside -->
            <rect x="268" y="198" width="54" height="78" rx="2" opacity=".45"/>
            <!-- air-source unit beside the house -->
            <rect x="508" y="256" width="46" height="44" rx="2" opacity=".5"/>
            <!-- ground loop under the garden -->
            <path d="M120 338 H236 M120 358 H236 M120 378 H236" opacity=".4"/>
            <path d="M120 338 V378 M236 338 V378" opacity=".4"/>
            <!-- turbine in the open garden -->
            <path d="M104 300 V196" opacity=".5"/>
            <circle cx="104" cy="190" r="4" opacity=".6"/>
            <path d="M104 186 L104 160 M104 186 L126 198 M104 186 L82 198" opacity=".5"/>
            <!-- driveway + charger -->
            <path d="M600 300 H792" stroke-width="2" opacity=".3"/>
            <rect x="614" y="262" width="26" height="38" rx="2" opacity=".5"/>
            <!-- grid connection at the boundary -->
            <path d="M846 300 V212" opacity=".5"/>
            <path d="M826 212 H866" opacity=".5"/>
            <path d="M846 240 H694" stroke-dasharray="4 4" opacity=".4"/>
          </g>
          <g font-family="Work Sans, sans-serif" font-size="10" fill="#1F3B2E"
             letter-spacing="1.4">
            <text x="382" y="112" font-size="9" fill="#4F6B4A">1</text>
            <text x="396" y="112">ROOF</text>
            <text x="276" y="192" font-size="9" fill="#4F6B4A">2</text>
            <text x="290" y="192">UTILITY / WALL</text>
            <text x="512" y="248" font-size="9" fill="#4F6B4A">3</text>
            <text x="526" y="248">AIR</text>
            <text x="124" y="332" font-size="9" fill="#4F6B4A">4</text>
            <text x="138" y="332">GROUND</text>
            <text x="76" y="152" font-size="9" fill="#4F6B4A">5</text>
            <text x="90" y="152">GARDEN</text>
            <text x="618" y="252" font-size="9" fill="#4F6B4A">6</text>
            <text x="632" y="252">DRIVEWAY</text>
            <text x="800" y="206" font-size="9" fill="#4F6B4A">7</text>
            <text x="814" y="206">GRID</text>
          </g>
          <g font-family="Work Sans, sans-serif" font-size="10" fill="#55605A">
            <text x="20" y="386">An ordinary house, in section. Not your house, and not a design for one.</text>
          </g>
        </svg>
        <p class="anat-cap">Seven positions, drawn by PlotNua. Which of them apply
          depends entirely on the property &mdash; its age, its boundaries, its
          orientation, whether it has off-street parking, whether it is a protected
          structure. Nothing here is a recommendation for any particular house.</p>
      </div>

      <!-- 1 . ROOF -->
      <div class="pos">
        <span class="pos-where">1 &middot; Roof</span>
        <h3>Generation</h3>
        <span class="ev">Today</span>
        <p>The one position almost every house has, and the only one with no moving
          parts. Panels turn daylight into electricity the house uses straight
          away.</p>
        <ul class="pos-facts">
          <li>
            <span class="dq-cat">Grant</span>
            <span class="dq-fact">&euro;700 per kWp for the first 2&nbsp;kWp, then
              &euro;200 for each additional kWp to 4&nbsp;kWp.</span>
            <span class="dq-note">A maximum of &euro;1,800 in 2026, paid pro rata.
              SEAI.</span>
          </li>
          <li>
            <span class="dq-cat">VAT</span>
            <span class="dq-fact">0% on the supply and installation of panels on a
              private dwelling.</span>
          </li>
          <li>
            <span class="dq-cat">Permission</span>
            <span class="dq-fact">No planning permission for rooftop panels on a
              house, and no limit on the roof area used.</span>
            <span class="dq-note">Restrictions still apply to protected structures
              and homes in an Architectural Conservation Area, and the exemption
              carries conditions such as a minimum distance from the roof
              edge.</span>
          </li>
          <li>
            <span class="dq-cat">Who qualifies</span>
            <span class="dq-fact">The home must have been built and occupied before
              2021, and the grant is not open where solar PV funding has already
              been claimed at that MPRN &mdash; whoever claimed it.</span>
            <span class="dq-note">Your installer applies to ESB Networks before
              anything goes on the roof. That usually takes at least four
              weeks.</span>
          </li>
        </ul>
        <div class="pos-open">SEAI&rsquo;s own words, worth knowing before you
          choose anyone: it <strong>&ldquo;does not approve, guarantee, or warranty
          a company or their works.&rdquo;</strong> The State pays part of the cost.
          Choosing the installer is still entirely yours.</div>
      </div>

      <!-- 2 . UTILITY / WALL SPACE -->
      <div class="pos">
        <span class="pos-where">2 &middot; Utility room, garage or wall space</span>
        <h3>Storage</h3>
        <span class="ev">Today</span>
        <p>A battery does not make electricity; it moves it through time. It holds
          the afternoon until the evening, and it is the piece that turns a house
          from something that reacts to the grid into something that can choose.</p>
        <ul class="pos-facts">
          <li>
            <span class="dq-cat">Grant</span>
            <!-- PN-DISC026-BATTERY-BOUNDARY-BEGIN
                 THE GOVERNED DATE BOUNDARY. Stated in ANNOUNCED form, with the
                 date on its face, so the sentence is true before 6 October 2026
                 and true after it. Converting it to the present tense on or
                 after that date is a single anchored edit INSIDE these markers
                 and is deliberately not part of this build. Do not remove the
                 markers; they are what makes that edit bounded. -->
            <span class="dq-fact">From 6 October 2026 SEAI is to pay a flat
              &euro;600 towards a home battery of 5&nbsp;kWh or larger.</span>
            <span class="dq-note">Announced by SEAI. Batteries under 5&nbsp;kWh are
              not eligible, and the amount is flat rather than scaled to
              size.</span>
            <!-- PN-DISC026-BATTERY-BOUNDARY-END -->
          </li>
          <li>
            <span class="dq-cat">Who qualifies</span>
            <span class="dq-fact">The home needs an MPRN and must have been built and
              occupied before 2025 &mdash; not 2021.</span>
            <span class="dq-note">The battery threshold is a different year from the
              solar one. A house finished in 2022 is outside the solar grant and
              inside this one. One per MPRN.</span>
          </li>
          <li>
            <span class="dq-cat">The grid side</span>
            <span class="dq-fact">ESB Networks treats an AC-connected battery as a
              microgenerator, listed on the NC6 application with its rated
              output.</span>
            <span class="dq-note">Within the microgeneration thresholds, assessed on
              inverter capacity. The notification happens before installation, not
              after.</span>
          </li>
        </ul>
      </div>

      <!-- 3 . AIR -->
      <div class="pos">
        <span class="pos-where">3 &middot; The air beside the house</span>
        <h3>Heat, taken from outside</h3>
        <span class="ev">Today</span>
        <p>A heat pump is the largest single change most Irish houses can make to how
          they use energy, and the one that most changes what the roof and the
          battery are for. An outdoor unit the size of a small chest freezer takes
          heat out of the air, even in winter, and moves it inside.</p>
        <ul class="pos-facts">
          <li>
            <span class="dq-cat">Grant</span>
            <span class="dq-fact">Up to &euro;14,500 for a detached, semi-detached or
              mid-terrace house, as a bundle.</span>
            <span class="dq-note">SEAI. The ceiling is lower for an apartment, and
              lower again for air-to-air.</span>
          </li>
          <li>
            <span class="dq-cat">The condition that catches people</span>
            <span class="dq-fact">The house has to be able to hold the heat first.
              SEAI uses a Heat Loss Indicator of 2.3 or below.</span>
            <span class="dq-note">If your house is above it, or nobody knows, a
              technical assessment establishes the position. Built and occupied
              before 2021.</span>
          </li>
        </ul>
        <div class="pos-open">This is the position where sequence matters most. A
          heat pump in a house that leaks heat is an expensive way to be cold, which
          is exactly why the Heat Loss Indicator exists.</div>
      </div>

      <!-- 4 . GROUND -->
      <div class="pos">
        <span class="pos-where">4 &middot; The ground beneath the garden</span>
        <h3>Heat, taken from below</h3>
        <span class="ev">Today</span>
        <p>A few metres down, the ground sits at roughly the same temperature all
          year. A ground-source system takes heat from there instead of from the air
          &mdash; either through pipework laid in shallow trenches across the
          garden, or down a borehole where there is no room to dig.</p>
        <ul class="pos-facts">
          <li>
            <span class="dq-cat">Grant</span>
            <span class="dq-fact">The same &euro;14,500 ceiling as an air-to-water
              system. Water-to-water likewise.</span>
            <span class="dq-note">SEAI. Ground-source is not a separate scheme and
              is not funded differently &mdash; it sits inside the same heat pump
              grant.</span>
          </li>
          <li>
            <span class="dq-cat">What decides it</span>
            <span class="dq-fact">Garden area for trenches, or access for a drilling
              rig. This is the one position where the shape of your site, not the
              house, is the constraint.</span>
          </li>
        </ul>
        <div class="pos-open">You will see ground-source described as giving
          &ldquo;free cooling&rdquo; in summer. <strong>PlotNua has not established
          whether, or on what terms, a domestic ground loop in Ireland can be used
          for cooling</strong>, so we are not going to tell you it can. We will say
          so when we have a first-party answer.</div>
      </div>

      <!-- 5 . GARDEN . The route where administrative possibility and site
           suitability must be visibly separated. Founder correction 2 withdrew
           a sentence that characterised the air at the exempt rotor height;
           the evidence does not establish it to the required standard, so it
           is not in this page and not quoted in this comment either. -->
      <div class="pos">
        <span class="pos-where">5 &middot; The open garden</span>
        <h3>Wind, and the gap between allowed and advisable</h3>
        <span class="ev">Today &mdash; legally and administratively</span>
        <p>A domestic wind turbine can be put up in Ireland without planning
          permission, connected under the same rules as solar, and paid for what it
          exports. That is genuinely true, and it is also only half the question.</p>
        <ul class="pos-facts">
          <li>
            <span class="dq-cat">The exempt envelope</span>
            <span class="dq-fact">13&nbsp;m total height. 6&nbsp;m rotor.
              3&nbsp;m clearance between the ground and the lowest point of the
              blades.</span>
            <span class="dq-note">One per house, not attached to the building, not
              sited in front of it. Matt finish, no advertising, no interference with
              telecoms signals. SEAI, summarising S.I. 83 of 2007 and S.I. 235 of
              2008.</span>
          </li>
          <li>
            <span class="dq-cat">The boundary rule</span>
            <span class="dq-fact">The mast must stand back from the nearest party
              boundary by the total height of the assembly plus one metre.</span>
            <span class="dq-note">At the 13&nbsp;m maximum that is a 14&nbsp;m clear
              radius. On most suburban sites this is the condition that decides the
              question, before wind is discussed at all.</span>
          </li>
          <li>
            <span class="dq-cat">Noise</span>
            <span class="dq-fact">43&nbsp;dB(A) or less, or no more than
              5&nbsp;dB(A) above background, at the nearest inhabited neighbouring
              dwelling.</span>
          </li>
          <li>
            <span class="dq-cat">Where the exemption disappears</span>
            <span class="dq-fact">It does not apply at all where the work would
              affect a protected landscape or view, protected archaeological,
              geological, historical, scientific or ecological features, or an area
              under a special amenity area order.</span>
            <span class="dq-note">Designations change under a house. SEAI advises a
              Section 5 Declaration from the local authority, about &euro;80, and
              warns: &ldquo;There have been instances of people assuming they were
              exempt which have ended with the local authority requesting that
              installations be removed.&rdquo;</span>
          </li>
          <li>
            <span class="dq-cat">Connecting it</span>
            <span class="dq-fact">ESB Networks&rsquo; micro-generation definition
              &ldquo;makes no explicit reference to any specific form of generating
              technology&rdquo;, so a domestic turbine goes through the same NC6
              route as solar.</span>
            <span class="dq-note">Micro-generation is 25&nbsp;A or less on a single
              phase, about 6&nbsp;kVA. Where generation is not inverter-connected
              &mdash; which small wind can be &mdash; capacity is assessed on the
              generator&rsquo;s own continuous rating.</span>
          </li>
          <li>
            <span class="dq-cat">Being paid for it</span>
            <span class="dq-fact">The regulator&rsquo;s definition of
              microgeneration names small wind turbines explicitly, so export is
              paid on the same terms as solar.</span>
            <span class="dq-note">CRU. There is <strong>no SEAI grant</strong> for a
              domestic wind turbine.</span>
          </li>
        </ul>
        <div class="pos-open"><strong>What is settled is what you may build and
          connect. What is not settled is whether it would be worth building at your
          property.</strong> PlotNua has not established realistic output,
          turbulence from surrounding buildings and trees, installation and
          maintenance costs, or credible Irish suppliers &mdash; and we will not
          estimate any of them from vendor material.<br><br>
          Two further cautions we would rather state than leave you to discover. The
          SEAI Wind Atlas is the obvious place to look and <strong>it cannot answer
          this question</strong>: its lowest height is 50&nbsp;m, and the tallest
          exempt domestic turbine is 13&nbsp;m. And the SEAI document that sets out
          the exemptions above is demonstrably out of date on solar, so the wind rule
          should be confirmed against current legislation before anyone relies on
          it.</div>
        <div class="rights">
          <b>No photograph, deliberately.</b> PlotNua has found no verified
          photograph of a compliant domestic turbine at an Irish property, and has
          asked an Irish installer whether a genuine domestic example exists. A farm
          or utility turbine must never illustrate the 13&nbsp;m domestic rule: it
          would misrepresent the one thing the evidence here is clearest about. The
          diagram above is what we can honestly show.
        </div>
      </div>

      <!-- 6 . DRIVEWAY -->
      <div class="pos">
        <span class="pos-where">6 &middot; The driveway</span>
        <h3>Charging, and the car as a battery</h3>
        <span class="ev">Today &mdash; charging</span>
        <p>A home charger needs somewhere off-street to put the car, which is the
          whole of the test. The more interesting question is the other direction of
          travel, and that one is not settled.</p>
        <ul class="pos-facts">
          <li>
            <span class="dq-cat">Today</span>
            <span class="dq-fact">Charging at home, on off-street parking, moved to
              whichever hours your supplier prices lowest.</span>
            <span class="dq-note">This is the single easiest thing on this page to
              change, and it costs nothing to change it.</span>
          </li>
          <li>
            <span class="dq-cat">Emerging</span>
            <span class="dq-fact">ESB Networks treats a car exporting to the grid as
              a generator, under the same micro-generation and mini-generation rules
              as solar, a battery or a turbine.</span>
            <span class="dq-note">It has published the architecture and standards it
              expects, including EN&nbsp;50549 with Irish protection settings,
              I.S.&nbsp;10101, EN&nbsp;ISO&nbsp;15118 for the vehicle interface and
              Safe Electric certification &mdash; and says to apply for the generator
              connection before choosing the car and charger.</span>
          </li>
        </ul>
        <div class="pos-open"><strong>PlotNua has not established when, or whether, a
          homeowner can actually buy this in Ireland.</strong> You will find
          confident dates for it online. We could not stand over any of them, so we
          are not repeating them.</div>
      </div>

      <!-- 7 . GRID CONNECTION -->
      <div class="pos">
        <span class="pos-where">7 &middot; The grid connection</span>
        <h3>Where the house meets everybody else&rsquo;s</h3>
        <span class="ev">Today</span>
        <p>The last position is the one nobody thinks of as part of the house. It is
          the piece that turns the other six from a private arrangement into
          something the system can see, use and pay for.</p>
        <ul class="pos-facts">
          <li>
            <span class="dq-cat">The meter</span>
            <span class="dq-fact">Over two million smart meters are installed, and
              more than four out of five households have one.</span>
            <span class="dq-note">ESB, September 2025. Having one does not put you on
              a time-of-use tariff &mdash; that is a separate choice with your
              supplier.</span>
          </li>
          <li>
            <span class="dq-cat">Export</span>
            <span class="dq-fact">Every electricity supplier must pay for eligible
              electricity you export.</span>
            <span class="dq-note">But not until the NC6 or NC7 has been processed by
              ESB Networks. Without that, the supplier will not pay. Rates are not
              regulated &mdash; each supplier sets its own.</span>
          </li>
          <li>
            <span class="dq-cat">Tax</span>
            <span class="dq-fact">The first &euro;400 a year of microgeneration
              income is exempt from income tax.</span>
          </li>
          <li>
            <span class="dq-cat">The trap</span>
            <span class="dq-fact">If a smart meter has been offered and refused, the
              home is not eligible for export payment at all.</span>
            <span class="dq-note">This one is worth checking if anybody in the house
              ever said no at the door.</span>
          </li>
        </ul>
      </div>
    </div>

    <details class="faq-item is-inline" style="margin-top:44px">
      <summary><h3>Grant, tax and permission in detail</h3><span class="icon"></span></summary>
      <div class="faq-a"><strong>Solar.</strong> &euro;700 per kWp for the first
        2&nbsp;kWp and &euro;200 for each additional kWp to 4&nbsp;kWp, to a maximum
        of &euro;1,800 in 2026, paid pro rata, with 0% VAT on supply and
        installation. The house must have been built and occupied before 2021. The
        grant can be claimed once at an MPRN, so if a previous owner claimed it, it
        is gone. Your installer applies to ESB Networks before anything goes on the
        roof and that usually takes at least four weeks; afterwards the house needs a
        new BER assessment before the grant is paid.<br><br>
        <strong>Battery.</strong> A flat &euro;600 for a system of 5&nbsp;kWh or
        larger, announced by SEAI to start on 6 October 2026. The home needs an MPRN
        and must have been built and occupied <em>before 2025</em> &mdash; a
        different year from the solar grant, and the reason a 2022 house can be
        outside one and inside the other. One per MPRN, installed by an SEAI
        registered Solar PV contractor, with the ESB Networks application made before
        installation. Solar and battery can go in a single application. Whether a
        battery installed before that date can be claimed retrospectively, and how
        the &euro;600 interacts with the solar ceiling, are two things PlotNua has
        <em>not</em> established and will not guess at.<br><br>
        <strong>Heat pump.</strong> Up to &euro;14,500 as a bundle for a detached,
        semi-detached or mid-terrace house, lower for an apartment and lower again
        for air-to-air. Ground-source and water-to-water sit inside the same ceiling.
        A Heat Loss Indicator of 2.3 or below, or a technical assessment to establish
        the position. Built and occupied before 2021.<br><br>
        <strong>Tax.</strong> The first &euro;400 a year from exporting is exempt from
        income tax. Above that it is taxed like other income.<br><br>
        <strong>Permission.</strong> Rooftop panels on a house are exempt with no area
        limit. A domestic wind turbine is exempt only inside the envelope set out
        above. Both exemptions fall away for protected structures, Architectural
        Conservation Areas and the landscape, amenity and heritage designations in
        your local development plan. If any of that might apply to your home, ask your
        local authority &mdash; and for a turbine, ask for a Section 5
        Declaration.<br><br>
        <strong>Who stands behind the work.</strong> SEAI &ldquo;does not approve,
        guarantee, or warranty a company or their works.&rdquo; The State pays part of
        the cost. It does not stand behind whoever does the job.</div>
    </details>

    <div class="rights">
      <b>Why there are no photographs of real Irish installations here yet.</b> Every
      position above deserves one &mdash; a real roof, a real battery on a real
      utility wall, a trench with a ground loop in it, a charger on a real driveway.
      PlotNua does not publish a supplier&rsquo;s photograph because it is visible on
      their website. Permission requests are out and unanswered, and until they come
      back these positions carry a diagram or nothing. The page is built so that a
      granted photograph drops into its position without anything else moving.
    </div>
  </section>
</main>

<section class="imagine-photo reveal">
  <!-- CONCEPT IMAGERY, position 1 of 2. The storyboard confines the five
       AI-generated DISC-026 images to the hero and to S8, and forbids them
       anywhere a claim of existence is being made. This is S8's opening and
       the frame is explicitly illustrative in the caption below.

       ASSET UNCHANGED. ce9da2e51c945693.jpg is also the governed Library card
       image for this Discovery; prove-discovery-library-images.mjs requires it
       to appear on this page with no potential-asset marker in its alt text. -->
  <img src="assets/img/ce9da2e51c945693.jpg" width="1408" height="768" loading="lazy" decoding="async"
       alt="An Irish family outside their home at dusk: solar panels across the roof, a battery unit in the open garage, a charger on the wall and an electric car in the driveway.">
  <div class="caption">
    <p>An illustration of the seven positions arriving on one property, not a
      photograph of a house that exists. Generated imagery, used here because the
      frame is explicitly about what a property could become.</p>
  </div>
</section>

<main class="article">

  <!-- ====================================================================
       S8 . WHAT COMES NEXT. Emerging and future, without overclaiming any
       of it. The plug-in solar material is founder-approved from
       26 September 2026 and is carried forward, compressed, because the
       evidence behind it is first-party and still stands.
       ==================================================================== -->
  <section class="article-section reveal" id="what-were-watching">
    <div class="kicker">What we&rsquo;re watching</div>
    <h2>The house is becoming a participant rather than a consumer.</h2>
    <span class="ev ev-emerging">Emerging and future</span>
    <p>Four things are moving at once. None of them is something you can act on this
      week, and all four change what the seven positions above are for.</p>

    <div class="dq-adv">
      <span class="dq-cat dq-adv-cat">Where each one actually stands</span>
      <ul class="dq-adv-cols is-four">
        <li>
          <span class="dq-adv-label">The hot water cylinder</span>
          <span class="dq-fact">Of everything in the house, the cylinder is the piece
            that connects the two halves of this page. It is the heat sink every
            household-scale compute model above depends on.</span>
          <span class="dq-note">Which is a strange thing to discover about the least
            interesting object in your utility room.</span>
        </li>
        <li>
          <span class="dq-adv-label">Solar that does not start on the roof</span>
          <span class="dq-fact">In Germany you can buy a small plug-in solar unit,
            hang it on a balcony railing and plug it in. More than a million
            households have registered one.</span>
          <span class="dq-note">Up to 2,000&nbsp;W of panels and an inverter of up to
            800&nbsp;VA, under the Bundesnetzagentur&rsquo;s published limits, with
            registration in the national register still required.</span>
        </li>
        <li>
          <span class="dq-adv-label">Ireland &mdash; being worked on</span>
          <span class="dq-fact">ESB Networks has convened a cross-industry group with
            the CRU and the NSAI to find a shared pathway, and has identified changes
            to its own standards and procedures.</span>
          <span class="dq-note">The group first met on 9 June 2026. ESB Networks
            estimated those changes would take up to twelve months, and a report to
            the Minister was expected in September 2026. Nothing has been published.
            <strong>Ireland does not yet have an established plug-in pathway for
            these smaller grid-connected systems.</strong></span>
        </li>
        <li>
          <span class="dq-adv-label">Houses working together</span>
          <span class="dq-fact">Sustainable Energy Communities exist in Ireland, and
            development-scale heat networks are already real &mdash; Tallaght is
            one.</span>
          <span class="dq-note">What is immature here is the framework that would let
            ordinary neighbouring houses share what they generate. That is the bridge
            between the energy half of this page and the compute half.</span>
        </li>
      </ul>
      <p class="dq-note" style="margin-top:18px"><strong>Today, a grid-connected
        micro-generator in Ireland still goes through ESB Networks.</strong> The
        inverter has to meet IS&nbsp;EN&nbsp;50549-1 with Irish settings, a type-test
        certificate goes with the form, and the notification is made for you by your
        registered installer. Until an Irish plug-in route is published, that is the
        rule &mdash; whatever is on sale elsewhere.</p>
    </div>

    <p style="margin-top:40px">Set the four of them beside the rest of this page and
      a shape appears. A plug-in panel on a balcony. The same panel with a small
      battery behind it. A full roof and a house battery. A development with its own
      heat network. <strong>They are not different products so much as different
      sizes of the same idea: a part of a property doing something with energy
      rather than only consuming it.</strong></p>
  </section>
</main>

<section class="imagine-photo reveal">
  <!-- CONCEPT IMAGERY, position 2 of 2. Asset unchanged and unedited. The
       caption carries the illustrative frame, as the rule requires. -->
  <img src="assets/img/f0e99db16cefc470.jpg" width="1376" height="768" loading="lazy" decoding="async"
       alt="An Irish housing estate seen from above at dusk, with solar panels on several of the roofs.">
  <div class="caption">
    <p>An illustration, not a survey. The street where the development-scale version
      of this would make sense is an ordinary one &mdash; which is the point, and
      also the part nobody has built yet.</p>
  </div>
</section>

<main class="article">

  <!-- ====================================================================
       S9 . WHAT PLOTNUA IS DOING ABOUT IT, then back to the flagship.
       Founder correction 3: the ending returns to the revelation.

       ABSOLUTE PROHIBITIONS AT THIS POINT. No suitability verdict. No score.
       No income implication. No register sign-up presented as a waiting list
       for a product. No "your house becomes a data centre".
       ==================================================================== -->
  <section class="article-section reveal">
    <div class="kicker">What PlotNua is doing about it</div>
    <h2>We can&rsquo;t assess your house for this. We can tell you what would be
      asked.</h2>
    <span class="ev">Today &mdash; the check exists</span>
    <p>There is a separate check that reads a property against what PlotNua can
      actually stand over, and tells you what is still to establish. It gives
      <strong>three states and no score</strong>, because a percentage would claim we
      know what 100% means. We do not, and a build gate stops a number reaching the
      page.</p>
    <p>It keeps four kinds of finding apart &mdash; what is present, what the gaps
      are, what is simply absent, and what is conditional &mdash; and
      <em>&ldquo;I don&rsquo;t know&rdquo;</em> is a real answer to every question in
      it. The two findings in the dark band above are emitted on every single run,
      whatever anyone answers.</p>

    <!-- THE CHAIN. The founder's sequence, with the status boundary visible
         inside it rather than asserted around it. -->
    <ol class="chain">
      <li><span class="chain-n">01</span><span class="chain-t">Generation
        <span>The roof. Available today, grant-supported, worth doing alone.</span></span></li>
      <li><span class="chain-n">02</span><span class="chain-t">Storage
        <span>The utility wall. Available today. The grant arrives 6 October 2026.</span></span></li>
      <li><span class="chain-n">03</span><span class="chain-t">Management
        <span>The meter and the tariff. Available today, and the cheapest step of all.</span></span></li>
      <li><span class="chain-n">04</span><span class="chain-t">An active energy property
        <span>Generating, storing, timing and exporting. Thousands of Irish homes are already here.</span></span></li>
      <li><span class="chain-n">05</span><span class="chain-t">Distributed compute
        <span>Operating in British and German homes. Not available in Ireland, and not on any Irish operator&rsquo;s pipeline for homes today.</span></span></li>
      <li><span class="chain-n">06</span><span class="chain-t">Useful compute heat
        <span>Real at district scale in Tallaght since 2023. Real at household scale abroad. Not connected to an Irish house by anyone.</span></span></li>
      <li><span class="chain-n">07</span><span class="chain-t">A house doing some of the work of a data centre
        <span>A possibility, not a product. Nobody has published what a property would have to be, which is why this page ends with a question instead of an offer.</span></span></li>
    </ol>

    <div class="handoff-pair" style="margin-top:44px">
      <div class="handoff">
        <h3>What your home could do today</h3>
        <p>A few short questions about this property, and we&rsquo;ll set out which
          of the four energy moves could apply here &mdash; and what&rsquo;s worth
          checking next. No quote at the end.</p>
        <a href="disc026-power-station.html">See what your home could do &rarr;</a>
      </div>
      <div class="handoff">
        <h3>The separate question</h3>
        <p>Could a house like this ever host computing? Nobody can answer that yet.
          This check tells you what would be asked, and what PlotNua has not
          established.</p>
        <a href="disc026-compute-readiness-check.html">Residential Compute Readiness &rarr;</a>
      </div>
    </div>
  </section>
</main>

<section class="closing-line reveal">
  <!-- FOUNDER CORRECTION 3. The ending returns to the flagship revelation,
       as a question, in the same words it was asked in. -->
  <p>So it stays a question, and it is still the right one. Could your house one day
    do some of the work of a data centre &mdash; and use the heat it creates?</p>
</section>"""

html = html[:i] + BODY + html[j:]


# ---------------------------------------------------------------------------
# 5 . POST-WRITE ASSERTIONS. A builder that does not check its own output is
#     a find-and-replace with a docstring.
# ---------------------------------------------------------------------------

checks = []


def must(cond, label):
    checks.append((bool(cond), label))


# Founder correction 2: the withdrawn sentence, in any casing.
must("worst air" not in html.lower(),
     "correction 2: the 'worst air' claim is absent")

# The two guarded assets and their alt-text contracts.
must(html.count("assets/img/fec77c3f0bae107a.jpg") == 1,
     "hero asset present exactly once")
must("annotated by PlotNua as a potential asset" in html,
     "hero keeps its potential-asset marker (library capability proof)")
must(html.count("assets/img/ce9da2e51c945693.jpg") == 1,
     "governed Library image present exactly once")
for marker in ("potential asset", "annotated by plotnua",
               "before anything is planted", "standing completely empty"):
    seg = html.split('assets/img/ce9da2e51c945693.jpg')[1][:400].lower()
    must(marker not in seg,
         "Library image alt carries no %r marker" % marker)

# The battery date boundary must be bounded and must not be present tense.
must(html.count("PN-DISC026-BATTERY-BOUNDARY-BEGIN") == 1
     and html.count("PN-DISC026-BATTERY-BOUNDARY-END") == 1,
     "battery boundary markers present exactly once each")
must("From 6 October 2026 SEAI is to pay a flat" in html,
     "battery grant is stated in announced form with its date on its face")

# No remote imagery, so the rights gate's remote scope stays untouched.
import re
remote = re.findall(r'<img[^>]+src="(https?://[^"]+)"', html)
must(not remote, "no remotely-hosted image (found %d)" % len(remote))

# Withdrawn claims must not have come back.
for gone in ("Hestiia", "myEko", "SPAN", "XFRA", "Sunrun", "Voltus", "Zai Node",
             "until 2028", "2027", "140,000"):
    must(gone not in html, "withdrawn claim %r is absent" % gone)

# The shell survived.
for keep in ('id="Cookiebot"', 'G-PKKJ0RK6N8',
             'rel="canonical"', 'class="pn-return"', 'id="brandMark"',
             'class="related reveal"', '<footer>',
             "document.querySelectorAll('.reveal')"):
    must(keep in html, "shell element preserved: %s" % keep)

# The nine sections, by their landmarks.
for s, mark in [
        ("S1", 'class="d-hero"'),
        ("S2", "A computer cannot stop making heat"),
        ("S3", "bolted to the hot water cylinder"),
        ("S4", "already heats buildings in Tallaght"),
        ("S5", "not part of the offering or the"),
        ("S6", 'class="seam reveal"'),
        ("S7", "The energy anatomy of your property"),
        ("S8", "a participant rather than a consumer"),
        ("S9", "We can&rsquo;t assess your house for this")]:
    must(mark in html, "%s present" % s)

# The seven anatomy positions, in order.
order = [html.find("1 &middot; Roof"),
         html.find("2 &middot; Utility room, garage or wall space"),
         html.find("3 &middot; The air beside the house"),
         html.find("4 &middot; The ground beneath the garden"),
         html.find("5 &middot; The open garden"),
         html.find("6 &middot; The driveway"),
         html.find("7 &middot; The grid connection")]
must(all(x > 0 for x in order) and order == sorted(order),
     "all seven anatomy positions present and in order")

# The honesty break must sit ABOVE the energy anatomy. If it ever slips below,
# the whole argument inverts and the grants read as part of the compute offer.
must(0 < html.find('class="seam reveal"') < html.find("The energy anatomy of your property"),
     "the honesty break precedes the energy anatomy")

# The two RCR findings, verbatim.
must("Distributed residential computing is not currently commercially" in html,
     "RCR finding 1 carried verbatim")
must("PlotNua will not pretend otherwise" in html,
     "RCR finding 2 carried verbatim")

# Tag balance on the rebuilt body.
must(html.count("<main") == html.count("</main>"), "main tags balanced")
must(html.count("<section") == html.count("</section>"), "section tags balanced")
# Four: the hero's Potential Asset annotation, plus the three new diagrams.
must(html.count("<svg") == html.count("</svg>") == 4,
     "four SVGs: the hero annotation and three PlotNua diagrams")

bad = [lab for ok, lab in checks if not ok]
print("DISC-026 DISCOVERY REBUILD")
print("=" * 74)
for ok, lab in checks:
    print("  %s  %s" % ("PASS" if ok else "FAIL", lab))
print("=" * 74)
if bad:
    print("REFUSED -- %d assertion(s) failed. Nothing written." % len(bad))
    sys.exit(2)

PAGE.write_text(html, encoding="utf-8")
print("WROTE %s (%d checks passed, %d bytes)" % (PAGE.name, len(checks), len(html)))
