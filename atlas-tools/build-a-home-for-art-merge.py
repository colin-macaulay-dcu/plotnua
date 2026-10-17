#!/usr/bin/env python3
"""A HOME FOR ART · merge DISC-024 into DISC-023 at the Discovery-page level.

Founder approval for build: 13 October 2026 ("A Home for Art · merged
Discovery · approved for build"). ONE homeowner-facing Discovery with three
branches; BOTH Property Checks stay independent journeys, unchanged (engines,
questions, outcomes, My Plot save keys). The Art Space Register stays closed
and untouched.

SOURCES ARE PINNED. The merged page is assembled from the two Discovery pages
exactly as they stood at BASE (460c97a, the approved baseline), read from git.
Every block of visible text on the new page must either appear verbatim in one
of those two pages or be founder-approved / interface wording declared in
NEW_TEXT below (guard M1). Nothing factual is written here from memory.

WRITES
  discovery-a-home-for-art.html          the merged Discovery
  discovery-open-your-home-to-art.html   a redirect page (not a Discovery):
                                         -> discovery-a-home-for-art.html#open-your-home-to-art,
                                         query string preserved
  and bounded one-for-one consolidation edits (CONSOLIDATION, below) to:
  index.html · discoveries.html · 404.html · your-plot.html · sitemap.xml ·
  disc024-open-your-home-to-art.html (its single back-link only) ·
  discovery-living-in-the-garden.html · discovery-your-home-on-screen.html ·
  atlas-tools/discovery-library-images.json · atlas-tools/build-search-index.py
  (the DISC-024 journey's parent possibility) · atlas-tools/prove-landmarks.mjs
  (the public Discovery list: 13 -> 12)

GUARDS
  M1  traceability: every visible text block is verbatim from BASE or declared
  M2  the three branch anchors and #before-anything-arrives exist exactly once
  M3  each Property Check is offered exactly once, in the one assessment
      section near the end, hosting first; the PlotArt homeowner button is the
      only other link (to the DISC-024 check); always with ?start=1 (two-option
      entry, 14 Oct 2026); the merged page links nowhere to the old URL.
      Amended 17 Oct 2026 (founder design decisions): previously required the
      checks to be linked from their branches and the closing panel.
      Amended again 17 Oct 2026 (EDITORIAL REDESIGN, founder decision 1): TWO
      placements of the same assessment section, one after the opening and one
      at the foot, each with one hosting card then one buying card
  M4  no new service claim: no loan/rental/placement/matching/booking offer
  M5  imagery: only images already published on the two source pages (plus one
      existing related-card thumbnail); no new asset file
  M6  every factual caution kept: insurance, custody, tax, planning, copyright,
      PlotArt and "not live yet" sentences present verbatim
  M7  redirect page: canonical to the merged page, query string preserved,
      hash target #open-your-home-to-art, no <main>, not in the sitemap
  M8  the DISC-024 check's ASSESSMENT is unchanged from BASE: the head
      scripts, the engine script, the My Plot save script, every question's
      variable and answer values, and the save call (journeyId and payload)
      are byte-identical; the Back control routes to the merged page; the
      founder-approved question wording (CHECK24_APPROVED) is present. The
      DISC-023 check equals BASE once the two-option entry and the declared
      result wording (CHECK23_WORDING, 17 Oct 2026) are reverted.
      Revised 14 Oct 2026 (founder UX direction): the check's PRESENTATION
      (layout, styles, result copy, the floating Back control) was redesigned,
      so a whole-page byte comparison no longer applies; what decides a
      result is still pinned to BASE.
  M9  every consolidation edit applied exactly once
  M10 the founder's hierarchy: hosting story first, Open > Live with > Discover & own,
      then PlotArt, then the assessment section (hosting card first). Amended
      17 Oct 2026: the artist plate follows the chooser, opening Possibility one.
      Amended again (EDITORIAL REDESIGN): opening -> top assessments -> empty wall
      -> in-page navigation (replacing the chooser) -> 01 + artist -> outcome ->
      02 + evening room -> 03 + same wall -> practical guide -> PlotArt ->
      closing assessments
  M11 ORIGINAL HOSTING IMAGERY (founder image correction, 13 Oct 2026): the hero
      is DISC-024's own published hero (dfb125ba9dd7cd87, DISC-024-03-Gallery-
      at-Home) with its own alt text; the hosting sequence follows it in its
      original order (046ec -> 6442d -> 05cab54); the buyer hero c0f5bf is not
      on the page; every card that represents this Discovery shows the hosting
      image
  M12 founder design decisions (17 Oct 2026): no two full-bleed images side by
      side; each check offered once (assessment section) and PlotArt once; the
      retired buttons, descriptions and invitation stay gone; Live with art
      carries its three routes and not the Display tile; corrections applied once.
      Extended 17 Oct 2026 (EDITORIAL REDESIGN): every photograph is its source
      <img> tag verbatim (file, alt, dimensions) and never two without a heading
      between; deep forest is a background only behind the assessments and
      terracotta never is; no two bands of one colour in a row; the headline
      cautions stay on view and every moved caution sits in a labelled
      expander; one labelled in-page navigation, in order, to real anchors.
      Mutation proof: atlas-tools/prove-a-home-for-art-redesign.py

Usage:
  python3 atlas-tools/build-a-home-for-art-merge.py --apply
  python3 atlas-tools/build-a-home-for-art-merge.py --check
"""
import html as htmllib
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
BASE = "460c97a"
MERGED = "discovery-a-home-for-art.html"
OLD = "discovery-open-your-home-to-art.html"
C23 = "disc023-buy-original-irish-art.html"
C24 = "disc024-open-your-home-to-art.html"
TARGET = MERGED + "#open-your-home-to-art"
# TWO-OPTION ENTRY (founder approval, 14 Oct 2026). Every link from this
# Discovery to a check carries ?start=1, so a homeowner who has just read the
# section begins at Question 1; the check's own intro, with its Start and
# Discover choices, is for visitors arriving from anywhere else. The entry
# itself is governed by atlas-tools/build-art-space-register.py (E0-E7).
START24 = C24 + "?start=1"
START23 = C23 + "?start=1"


def die(msg):
    print("REFUSED: " + msg + " -- nothing written")
    sys.exit(2)


def base(path):
    try:
        return subprocess.run(["git", "-C", str(ROOT), "show", "%s:%s" % (BASE, path)],
                              capture_output=True, text=True, check=True).stdout
    except subprocess.CalledProcessError:
        die("BASE %s is not available in git" % BASE)


A0 = base(MERGED)
O0 = base(OLD)


def once(src, needle, label):
    if src.count(needle) != 1:
        die("anchor not found exactly once in %s: %s" % (label, needle[:70]))
    return src.index(needle)


def section(src, start, label):
    """From the line that starts the section to its closing tag, inclusive."""
    i = once(src, start, label)
    i = src.rindex("  <section", 0, i)
    j = src.index("  </section>\n", i) + len("  </section>\n")
    return src[i:j]


def plate(src, img, label):
    i = once(src, img, label)
    i = src.rindex("<section class=\"imagine-photo", 0, i)
    j = src.index("</section>\n", i) + len("</section>\n")
    return src[i:j]


XLINK_A = re.compile(r"<!-- PLOTNUA-ART-XLINK --><br><br>.*?</span>", re.S)
XLINK_O = re.compile(r"\n\s*<span class=\"dq-note\"><!-- PLOTNUA-ART-XLINK -->.*?</span></span>", re.S)

# ---------------------------------------------------------------- fragments --
A_WHY = section(A0, '<div class="kicker">Why This Discovery?</div>', "A why")
A_IMG_WALL = plate(A0, 'src="assets/img/5dc201bef1868b84.jpg"', "A wall plate")
A_BUYING = section(A0, '<div class="kicker">What You Are Actually Buying</div>', "A buying")
A_IMG_SAME = plate(A0, 'src="assets/img/c1d46445b6a79373.jpg"', "A same-wall plate")
A_SIZE = section(A0, '<div class="kicker">Getting It Right</div>', "A size")
A_IMG_STUDIO = plate(A0, 'src="assets/img/5d43b14a51cf511f.jpg"', "A studio plate")
A_LOOK = section(A0, '<div class="kicker">Where To Look</div>', "A look")
A_COMM = section(A0, '<div class="kicker">Commissioning</div>', "A commissioning")
A_BEFORE = section(A0, '<div class="kicker">Before You Buy</div>', "A before you buy")
A_FAQ = XLINK_A.sub("", section(A0, '<div class="kicker">Frequently Asked Questions</div>', "A faq"))
A_IMG_EVENING = plate(A0, 'src="assets/img/571594a8d5b2e80a.jpg"', "A evening plate")
A_FUTURE = section(A0, '<div class="kicker">Where This Could Go</div>', "A future")

i = once(O0, "Making the work is rarely an artist&rsquo;s hardest problem.", "O first")
O_FIRST = O0[O0.rindex("  <section", 0, i):O0.index("  </section>\n", i) + len("  </section>\n")]
O_IMG_PA = plate(O0, 'src="assets/img/046ec577a454599b.jpg"', "O potential plate")
O_SETTLE = section(O0, '<div class="kicker">Before Anything Arrives</div>', "O settle")
O_IMG_ARTIST = plate(O0, 'src="assets/img/6442d19ec2dd1df0.jpg"', "O artist plate")
O_BETTER = XLINK_O.sub("", section(O0, '<div class="kicker">And afterwards</div>', "O better off"))
O_IMG_OUTCOME = plate(O0, 'src="assets/img/05cab54ac0af83d0.jpg"', "O outcome plate")
O_FUTURE = section(O0, "<h2>What if PlotNua could help you find each other?</h2>", "O future")

if "PLOTNUA-ART-XLINK" in A_FAQ + O_BETTER:
    die("cross-link remnants survived extraction")

# The hosting page's ported decision-board CSS (it carries .dq-adv, .dq-qual,
# .dq-fig, .is-four, .is-inline and .pa-frame, which the buyer page lacks).
ci = O0.index("  /* ==================================================================\n     PORTED FROM THE FROZEN DISCOVERIES")
cj = O0.index("/* PLOTNUA LANDMARKS v1", ci)
PORTED_CSS = O0[ci:cj]

# ------------------------------------------------------- approved new text --
HERO_SUB = "Your home could be more than somewhere to hang art."
HERO_INTRO = "Three possibilities. One home. And you decide how far to go."
# ORDER ALIGNED (founder design decisions, 17 Oct 2026): the lede names the
# three possibilities in the page's own order, host -> live with -> own.
LEDE = ("An original artwork could become part of your everyday life. You might offer space that helps an "
        "artist reach a new audience, experience an artist&rsquo;s work in your home before deciding whether "
        "to buy it, or discover a piece to own.")
INTRO_KICKER = "Where to start"
B1 = ("Discover &amp; own", "Find, buy or commission original Irish art.")
B2 = ("Live with art", "Explore experiencing an artist&rsquo;s finished work in your home by direct arrangement.")
B3 = ("Open your home to art", "Offer space to store, display, exhibit or potentially help sell artwork.")
B2_P1 = ("Some artists and galleries may agree to let you experience an artwork in your home before "
         "purchasing it. Others may consider temporary displays by individual arrangement.")
B2_P2 = ("PlotNua does not currently arrange artwork loans, rentals or placements. Any arrangement would "
         "need to be agreed directly with the artist or gallery.")
OVERLOOKED_H2 = "You may already have something an artist needs."
HOST_HERO_ALT = re.search(r'<img id="dHeroImg"[^>]*alt="([^"]*)"', O0).group(1)
# IMAGE CORRECTION (founder, 13 Oct 2026, 20:45): the merged Discovery opens on
# the hosting Discovery's own hero, verbatim from BASE, not the buyer hero.
HOST_HERO_TAG = re.search(r'  <img id="dHeroImg"[^>]*>', O0).group(0)
BUY_HERO_TAG = re.search(r'  <img id="dHeroImg"[^>]*>', A0).group(0)
HOST_HERO = "assets/img/dfb125ba9dd7cd87.jpg"
BUY_HERO = "assets/img/c0f5bfcde033dea3.jpg"
if HOST_HERO not in HOST_HERO_TAG or BUY_HERO not in BUY_HERO_TAG:
    die("M11 the BASE heroes are not the recorded images")
CHECK23 = "Check your wall"
CHECK24 = "Check how far you&rsquo;d go"
SUB23 = ("Five short questions about the wall itself, and we&rsquo;ll set out what it will take, what to "
         "settle first, and where to start looking. No address, no measuring, and no price.")
SUB24 = ("Five short questions about the space you have and how far you&rsquo;d want this to go &mdash; then "
         "what you&rsquo;d need to settle before anything arrived. No address, no contact details, and nothing "
         "sent anywhere.")
ARTIST_PAGE = "artist-register.html"
# FOUNDER DESIGN DECISIONS (17 Oct 2026). Three presentation problems fixed:
# the two hosting plates were stacked, the two checks were offered seven times
# in five places, and the PlotArt registers were invited twice. Wording below is
# the founder's, verbatim, unless marked as interface or correction wording.
#
# 1 · ONE ASSESSMENT SECTION near the end (replaces every branch check button
#     and the old two-check panel). Founder wording; the two eyebrows are
#     interface labels that make the cards clearly different at a glance.
ASSESS_H = "What could art mean for your home?"
ASSESS_INTRO = "Explore the possibilities with two short, private checks."
CARD_HOST = ("For your space", "Could your home host art?",
             "Explore whether your space could store, display or host artwork.", "Explore my space")
CARD_OWN = ("For your walls", "Could original art work in your home?",
            "Explore choosing, buying or commissioning artwork for your walls.", "Explore art for my home")
ASSESS_NOTE = "Five short questions. No address or personal details required."
# 2 · ONE PLOTART SECTION after the three possibilities, at the PlotArt anchor
#     (replaces the top-of-page "Be part of the idea" invitation and the
#     two-card "Take part" section). Founder heading, introduction and button
#     labels; the note keeps the expressions-of-interest wording of 14 Oct and
#     adds the founder's "not currently matching participants or arranging
#     exhibitions", plus one line so a homeowner knows the button starts the
#     existing check, whose result offers the existing Art Space Register.
PLOTART_H = "Help bring art into more homes"
PLOTART_P = ("PlotArt is exploring ways to connect Irish artists with homeowners who have space to display, "
             "exhibit or potentially sell original artwork.")
PLOTART_B1 = "I have space for art"
PLOTART_B2 = "I&rsquo;m an artist looking for space"
PLOTART_NOTE = ("Both are expressions of interest only: free, private and non-binding. PlotNua is not currently "
                "matching participants or arranging exhibitions, and has not verified any space or artist.")
PLOTART_HOME_NOTE = ("If you have space, five short questions come first; at the end, you can choose to join "
                     "the Art Space Register.")
# 3 · LIVE WITH ART, "What if the gallery came to your home?" (founder idea).
#     Three routes, each written as something a third party may offer: no
#     provider is named, nothing is promised, and B2_P1 / B2_P2 stay verbatim
#     (M6). Evidence, 17 Oct 2026 (governance/A-HOME-FOR-ART-DESIGN-2026-10-17.md):
#     on approval -- this page's own FAQ, and Irish galleries advertising it;
#     home viewing -- at least one Irish artist publishes free home viewings
#     first-party; rental -- Irish rental services exist, at least one offering
#     rental to a home as well as a business. The duplicated Display tile is gone.
LIVE_Q = "What if the gallery came to your home?"
LIVE_CAT = "Three ways it can happen"
LIVE_ROUTES = (
    ("Try it at home", "You may be able to live with a chosen work for a few days before you decide.",
     "Some galleries and artists offer this on approval. It is a courtesy rather than a right, so ask "
     "&mdash; and ask who insures the work while it is with you."),
    ("A home viewing", "Some artists and galleries bring a selection of work to your home.",
     "You see it on your own walls, in your own light. Ask whether there is a charge, how much they bring, "
     "and whether you are under any obligation to buy."),
    ("Rental, where available", "A handful of Irish services rent original work by the month.",
     "Most are aimed at film, corporate and design clients, though at least one also rents to homes. Ask "
     "about the minimum term and who insures the work."),
)
LIVE_NOT_PLOTNUA = "Whether any of these is on offer is up to the artist or gallery."
# 5 · EDITORIAL REDESIGN (founder approval to build locally, 17 Oct 2026). Interface
#     labels only: the in-page navigation, the three numerals, and the one label
#     over the folded buying detail. Nothing factual is added.
MORE_LABEL = "More on buying and commissioning"
# 4 · FACTUAL CORRECTIONS (audit 17 Oct 2026, founder approval 17 Oct 2026).
#     Each pair is applied exactly once to the assembled page; the new text is
#     declared below for M1. Official-body links only, verified 17 Oct 2026.
_X = ' target="_blank" rel="noopener"'
CORRECTIONS = (
    # Culture Night: the dated 2026 sentence had passed; evergreen, and credited
    # as culturenight.ie credits it. The 1,800 figure was press-only and
    # inconsistent between sources, so it is dropped rather than restated.
    ("Artists open their working spaces and you can buy on the spot. Culture Night runs nationwide on 18 "
     "September 2026, free, through local authority arts offices &mdash; more than 1,800 events in 2025.",
     'Artists open their working spaces and you can buy on the spot. <a href="https://culturenight.ie/"%s>'
     'Culture Night</a> runs nationwide every September, free, coordinated by the Arts Council with local '
     'authorities.' % _X),
    ("A gallery represents its artists and handles the sale. Visual Artists Ireland describes a 50/50 split as "
     "standard, though it varies.",
     'A gallery represents its artists and handles the sale. <a href="https://visualartists.ie/how-to-manual/'
     'artists-commercial-galleries-the-international-art-market"%s>Visual Artists Ireland</a> describes a 50/50 '
     'split as standard, though it varies.' % _X),
    # RHA: the 196th Annual ran 25 May-9 Aug 2026; all works are for sale except
    # portraits. RDS: the Visual Art Awards exhibition opens in November (6 Nov
    # 2026-23 Jan 2027), artists chosen by curators from graduate exhibitions.
    ("Art Source fills the RDS each November. The RHA Annual Exhibition runs free through the summer, "
     "everything for sale. The RDS Visual Art Awards show graduate work each winter.",
     'Art Source fills the RDS each November. The <a href="https://rhagallery.ie/rha-annual/"%s>RHA Annual '
     'Exhibition</a> runs free from late spring through the summer, with almost everything for sale. The '
     '<a href="https://www.rds.ie/rds-foundation/arts/vaa"%s>RDS Visual Art Awards</a> exhibition opens each '
     'November, showing emerging artists chosen from graduate shows.' % (_X, _X)),
    # Revenue Form 12 (2025): net assessable non-PAYE income of EUR 5,000 or
    # more, or gross non-PAYE income of EUR 30,000 or more. "Reaches" was right
    # for the net test; the sentence now says net and carries the gross test.
    ("If your non-PAYE income for the year reaches &euro;5,000, Revenue treats you as a chargeable person and "
     "a different return applies.",
     "If your net non-PAYE income for the year reaches &euro;5,000, or your gross non-PAYE income reaches "
     "&euro;30,000, Revenue treats you as a chargeable person and a different return applies."),
    # Rental FAQ: at least one Irish rental service now also rents to homes.
    ("Yes. A handful of Irish services rent artwork monthly, though these are aimed mainly at film, corporate and "
     "design clients rather than households. Rotating works you already own between rooms costs nothing.",
     "Yes. A handful of Irish services rent artwork monthly. Most are aimed at film, corporate and design "
     "clients, though at least one also rents to homes. Rotating works you already own between rooms costs "
     "nothing."),
)
# Retired 17 Oct 2026 and refused by M12 if they return: the branch check
# buttons and their descriptions, the top-of-page invitation and the two-card
# "Take part" section.
RETIRED = ("Check how far you&rsquo;d go", "Check your wall", "Be part of the idea", "<!-- PLOTNUA-BE-PART",
           "Check this against your own home", "class=\"hfa-cta\"",
           "Five short questions about the space you have and how far you&rsquo;d want this to go",
           "Five short questions about the wall itself",
           # retired by the editorial redesign (17 Oct 2026): the three chooser
           # cards, replaced by the in-page navigation
           'class="hfa-paths"', "Which sounds like you?")
# Interface wording (labels, signposts) — new, non-factual, declared.
NEW_TEXT = ["A Home for Art", OVERLOOKED_H2, "The overlooked opportunity", HERO_SUB, HERO_INTRO, LEDE, B1[0], B1[1], B2[0], B2[1], B3[0], B3[1], B2_P1, B2_P2,
            "Possibility one", "Possibility two", "Possibility three", INTRO_KICKER, "Which sounds like you?",
            "Before anything arrives, the custody, insurance and money questions below apply here too.",
            "If you come to love the work:", "Finding each other",
            "Explore What Could You Build in Your Garden? &rarr;", "See all Discoveries &rarr;",
            "Back to the homepage", "Continue Exploring", "Related Discoveries", "Underused Ground",
            "The Borrowed Garden", "Room To Build", "What Could You Build in Your Garden?", "On Screen",
            "Your Home on Screen", "Explore another possibility",
            ASSESS_H, ASSESS_INTRO, ASSESS_NOTE, PLOTART_H, PLOTART_P, PLOTART_B1, PLOTART_B2, PLOTART_NOTE,
            PLOTART_HOME_NOTE, LIVE_Q, LIVE_CAT, LIVE_NOT_PLOTNUA] + list(CARD_HOST) + list(CARD_OWN) + \
           [x for r in LIVE_ROUTES for x in r] + [new for _, new in CORRECTIONS] + \
           ["01", "02", "03", "01 Open", "02 Live with", "03 Own", "Practical guide", "Checks", MORE_LABEL]

TITLE = "A Home for Art: Host, Live With or Buy Original Irish Art | PlotNua"
# META DESCRIPTION (founder design decisions, 17 Oct 2026): was 212 characters
# and truncated in results; now 153, hosting first, same three ideas, and "by
# arrangement" kept so it cannot read as a PlotNua service (independent review).
DESC = ("Open your home to an artist&rsquo;s work, live with art by arrangement, or find and commission "
        "original Irish art. What to agree, insure and settle in Ireland.")
OG_T = "A Home for Art | PlotNua Discoveries"
OG_D = "Your home could be more than somewhere to hang art. Three possibilities, one home, and you decide how far to go."

MERGE_CSS = """<style>/* PLOTNUA-HOME-FOR-ART-MERGE · generated by atlas-tools/build-a-home-for-art-merge.py.
   EDITORIAL REDESIGN (founder approval to build locally, 17 Oct 2026). Existing PlotNua
   colours only, each with one job:
     warm ivory  #F8F5EC  reading surfaces (opening, 01, 03, questions, PlotArt)
     deep forest #1F3B2E  the two assessment bands ONLY (M12 refuses it anywhere else)
     muted sage  #EEF2E8  02 Live with art
     warm stone  #EFE9DA  the ladder band and the practical guide
     terracotta  #BD6A46  numerals, thin rules and the PlotArt top edge; #A4532F for small
                          text. Never a background (M12).
   Photographs: full-bleed (wall, outcome), split (artist, same wall) and inset (evening);
   full frame on desktop, nothing regenerated or replaced. */
  .article-section p.hfa-lede{ font-family:'Fraunces',Georgia,serif; font-size:clamp(20px,2.3vw,25px);
    line-height:1.55; color:var(--ink); max-width:40ch; margin:0 0 30px; }
  .hfa-opening .dq-opp{ margin-top:34px; }

  /* ---- colour bands */
  .hfa-band.is-sage{ background:#EEF2E8; }
  .hfa-band.is-stone{ background:#EFE9DA; }
  .hfa-band.is-forest{ background:#1F3B2E; color:#F8F5EC; }
  .hfa-band .article-section{ border-bottom:none; padding:84px 0; }
  .hfa-band .article-section + .article-section{ padding-top:56px; border-top:1px solid rgba(31,59,46,.14); }
  .hfa-band .dq-adv-cols > li, .hfa-band .dq-qual > li{ background:#F8F5EC; }
  .hfa-band.is-stone .article{ max-width:1240px; }
  .hfa-band.is-stone .article-section p{ max-width:66ch; }

  /* ---- numerals, branch openings and the pull-quote */
  .hfa-num{ display:block; font-family:'Fraunces',Georgia,serif; font-weight:300;
    font-size:clamp(64px,7.4vw,108px); line-height:.86; letter-spacing:-.035em; color:#BD6A46; margin:0 0 22px; }
  .article-section p.hfa-branch-lead{ font-size:18.5px; line-height:1.65; color:var(--soft); max-width:42ch; }
  .article-section p.hfa-pull{ font-family:'Fraunces',Georgia,serif; font-size:clamp(18px,1.7vw,20px);
    line-height:1.6; color:var(--ink); border-left:2px solid #BD6A46; padding:2px 0 2px 22px; margin-top:34px;
    max-width:36ch; }
  .hfa-pull strong{ display:block; font-weight:500; font-size:clamp(22px,2.3vw,28px); line-height:1.3; margin-bottom:8px; }

  /* ---- the sticky in-page navigation: a compact pill in the same family as the
     brand mark, Search and Back. It sits between them, never over them, and
     scrolls away with the main column before the closing assessment band. */
  .hfa-nav-wrap{ position:sticky; top:22px; z-index:45; display:flex; justify-content:center;
    margin:34px 0; pointer-events:none; }
  .hfa-nav{ pointer-events:auto; max-width:calc(100% - 444px); background:#F8F5EC;
    border:1px solid rgba(31,59,46,.16); border-radius:24px; box-shadow:0 2px 10px rgba(31,59,46,.13); overflow:hidden; }
  .hfa-nav-list{ list-style:none; margin:0; padding:0 5px; display:flex; gap:2px; overflow-x:auto;
    scrollbar-width:none; -webkit-overflow-scrolling:touch; }
  .hfa-nav-list::-webkit-scrollbar{ display:none; }
  .hfa-nav-list li{ flex:0 0 auto; display:flex; }
  .hfa-nav a{ display:flex; align-items:center; gap:7px; min-height:44px; padding:0 14px; white-space:nowrap;
    font-family:'Work Sans',sans-serif; font-size:13.5px; font-weight:500; letter-spacing:.01em;
    color:var(--ink); text-decoration:none; border-radius:20px; transition:background .2s ease, box-shadow .2s ease; }
  .hfa-nav a:hover{ background:rgba(31,59,46,.06); }
  .hfa-nav a[aria-current]{ background:rgba(31,59,46,.07); box-shadow:inset 0 -2px 0 #BD6A46; }
  .hfa-nav a:focus-visible{ outline:2px solid var(--accent); outline-offset:-4px; }
  .hfa-nav-n{ font-family:'Fraunces',Georgia,serif; font-size:13px; font-weight:600; color:#A4532F; }
  #open-your-home-to-art, #live-with-art, #discover-and-own, #before-anything-arrives, #discover-your-property,
  #hfa-checks-top{ scroll-margin-top:84px; }

  /* ---- split photograph and text (01 and, mirrored, 03). Full frame on
     desktop: the picture takes its height from the image, nothing cropped. */
  .hfa-split{ display:grid; grid-template-columns:minmax(0,1fr) minmax(0,1.45fr); align-items:center; }
  .hfa-split.is-mirror{ grid-template-columns:minmax(0,1.45fr) minmax(0,1fr); }
  .hfa-split.is-mirror .hfa-photo{ order:-1; }
  .hfa-split-text.article-section{ padding:9.5vh 60px 9.5vh 7vw; border-bottom:none; max-width:640px; justify-self:end; }
  .hfa-split.is-mirror .hfa-split-text.article-section{ padding:9.5vh 7vw 9.5vh 60px; justify-self:start; }
  .hfa-photo{ position:relative; margin:0; overflow:hidden; background:rgba(31,59,46,.08); }
  .hfa-photo img{ display:block; width:100%; height:auto; aspect-ratio:1408 / 768; }
  .hfa-cap{ position:absolute; z-index:2; left:0; right:0; bottom:0; padding:44px 6% 22px;
    background:linear-gradient(180deg, rgba(15,14,10,0) 0%, rgba(15,14,10,.46) 100%); text-align:center; }
  .hfa-cap p{ font-family:'Fraunces',serif; font-style:italic; font-weight:400; color:#F8F5EC;
    font-size:clamp(16px,1.6vw,19px); line-height:1.45; max-width:34ch; margin:0 auto;
    text-shadow:0 1px 16px rgba(0,0,0,.3); }

  /* ---- inset photograph, framed inside the 02 band */
  .hfa-inset.hfa-photo{ position:relative; left:50%; translate:-50% 0; width:min(1100px, 86vw);
    margin:48px 0 54px; border-radius:2px; box-shadow:0 34px 64px -34px rgba(31,59,46,.5); }

  /* ---- full-bleed plates: a little shorter than 84vh, still a full screen's worth */
  #pn-main .imagine-photo:not(.pa-frame){ height:80vh; height:80svh; }

  /* ---- the ladder band: four compact tiles, then three people in one row */
  .hfa-ladder .dq-adv{ margin-top:0; }
  .hfa-band .dq-adv .dq-rows{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:0 34px; margin-top:6px; }
  .hfa-band .dq-adv .dq-rows > li, .hfa-band .dq-adv .dq-rows > li:first-child{ margin:0; padding-top:16px;
    border-top:1px solid rgba(31,59,46,.16); }
  .hfa-band .dq-rows .dq-fact{ font-size:17px; line-height:1.45; }

  /* ---- 03: the four routes as cards; the buying detail behind labelled expanders */
  .hfa-own .article-section{ padding:64px 0; }
  .hfa-own .article-section:first-child{ padding-top:76px; }
  #pn-main .article-section p a:not(.hfa-jump){ color:var(--ink); text-decoration:underline;
    text-decoration-color:rgba(31,59,46,.38); text-underline-offset:3px; }
  #pn-main .article-section p a:not(.hfa-jump):hover{ text-decoration-color:var(--ink); }
  #pn-main .article-section p a:not(.hfa-jump):focus-visible{ outline:2px solid var(--accent); outline-offset:2px; }
  .hfa-routes .practical-group{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:12px; margin-top:24px; }
  .hfa-routes .practical-item, .hfa-routes .practical-item:first-child{ background:#F8F5EC; padding:24px 26px 26px;
    border:1px solid rgba(31,59,46,.12); border-top:2px solid #BD6A46; border-radius:2px;
    box-shadow:0 1px 2px rgba(31,59,46,.05), 0 12px 22px -18px rgba(31,59,46,.3); }
  .hfa-routes .practical-item p{ font-size:15.5px; line-height:1.7; }
  .hfa-routes .practical-group + p{ margin-top:30px; }
  .hfa-cost .planning-sub{ margin-top:0; }
  .hfa-cost .planning-note{ margin-top:22px; padding-top:18px; }
  .faq-item.hfa-more{ border:1px solid rgba(31,59,46,.12); border-radius:2px; background:#F8F5EC;
    padding:0 24px; margin-top:10px; box-shadow:0 1px 2px rgba(31,59,46,.05), 0 10px 18px -16px rgba(31,59,46,.3); }
  .faq-item.hfa-more:last-child{ border-bottom:1px solid rgba(31,59,46,.12); }
  .faq-item.hfa-more summary{ padding:20px 0; }
  .faq-item.hfa-more summary h3{ font-family:'Fraunces',Georgia,serif; font-weight:500;
    font-size:clamp(18px,1.9vw,21px); line-height:1.35; }
  .hfa-more-k{ display:block; font-family:'Work Sans',sans-serif; font-size:11px; font-weight:500;
    letter-spacing:.16em; text-transform:uppercase; color:var(--accent); margin-bottom:6px; }
  .hfa-more-body{ padding:0 0 28px; }
  .hfa-more-body > p:first-child{ margin-top:0; }
  .article-section p.hfa-more-label{ font-family:'Work Sans',sans-serif; font-size:12px; letter-spacing:.16em; text-transform:uppercase;
    color:var(--accent); margin:0 0 14px; }

  /* ---- readable small type inside the main column (no tiny labels) */
  #pn-main .dq-cat, #pn-main .dq-adv-label{ font-size:10.5px; }
  #pn-main span.dq-note{ font-size:13.5px; }
  #pn-main .dq-use .dq-note{ font-size:13px; }
  #pn-main .dq-earn-caveat{ font-size:13.5px; }
  #pn-main .faq-item.is-inline summary h3{ font-size:12px; letter-spacing:.18em; }
  #pn-main .quiet-section .kicker{ opacity:1; }

  /* ---- assessments: the same two checks, top and bottom, on deep forest */
  .hfa-assess{ padding:88px 0 92px; text-align:center; }
  .hfa-assess-h{ font-family:'Fraunces',Georgia,serif; font-weight:400; font-size:clamp(28px,3.6vw,42px);
    line-height:1.22; letter-spacing:-.01em; color:#F8F5EC; margin:0 auto 12px; max-width:20ch; }
  .hfa-assess-intro{ font-size:17px; line-height:1.6; color:rgba(248,245,236,.86); margin:0 auto 36px; max-width:42ch; }
  .hfa-checks{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:20px; width:100%; max-width:880px;
    margin:6px auto 0; text-align:left; }
  .hfa-check{ display:flex; flex-direction:column; padding:30px 30px 32px; border-radius:2px;
    background:rgba(248,245,236,.07); border:1px solid rgba(248,245,236,.18); border-top:3px solid #BD6A46; }
  .hfa-check .hfa-check-k{ font-family:'Work Sans',sans-serif; font-size:11.5px; letter-spacing:.18em; text-transform:uppercase;
    color:#C9D8C2; margin:0 0 12px; line-height:1.4; }
  .hfa-check h3{ font-family:'Fraunces',Georgia,serif; font-weight:400; font-size:clamp(23px,2.4vw,28px); line-height:1.26;
    margin:0 0 10px; color:#F8F5EC; }
  .hfa-check p{ font-size:16px; line-height:1.6; color:rgba(248,245,236,.84); margin:0 0 26px; }
  .hfa-check .btn-primary{ margin-top:auto; align-self:flex-start; text-decoration:none; background:#F8F5EC; color:#1F3B2E;
    font-weight:600; }
  .hfa-check .btn-primary:hover{ background:#fff; }
  .hfa-check .btn-primary:focus-visible{ outline:2px solid #F8F5EC; outline-offset:3px; }
  .hfa-assess-note{ margin:24px auto 0; font-size:15px; line-height:1.6; color:rgba(248,245,236,.82); }
  #discover-your-property{ background:#1F3B2E; border-top:none; padding:96px 7vw 88px; }
  #discover-your-property .pn-wordmark, #discover-your-property .pb-headline{ color:#F8F5EC; }
  #discover-your-property .pb-subhead{ color:rgba(248,245,236,.86); }
  #discover-your-property .cs-exits{ margin-top:40px; }
  #discover-your-property .cs-exit{ color:#F8F5EC; border-bottom-color:rgba(248,245,236,.42); }
  #discover-your-property .cs-exit:hover{ border-bottom-color:#F8F5EC; }
  #discover-your-property .cs-exit.is-home{ color:rgba(248,245,236,.8); border-bottom-color:rgba(248,245,236,.3); }
  #discover-your-property .cs-exit:focus-visible{ outline-color:#F8F5EC; }

  /* ---- LIVE WITH ART · the gallery comes to you */
  .hfa-live-q{ font-family:'Fraunces',Georgia,serif; font-weight:400; font-size:clamp(22px,2.4vw,28px); line-height:1.3;
    color:var(--ink); margin:0 0 14px; max-width:28ch; }
  #live-with-art .dq-adv + p{ margin-top:30px; }

  /* ---- the one PlotArt section, terracotta-topped */
  .hfa-plotart{ margin:40px 0 0; padding:32px 32px 34px; background:#F8F5EC; border:1px solid rgba(31,59,46,.12);
    border-top:3px solid #BD6A46; border-radius:2px; box-shadow:0 1px 2px rgba(31,59,46,.05), 0 16px 30px -22px rgba(31,59,46,.34); }
  .hfa-plotart h3{ font-family:'Fraunces',Georgia,serif; font-weight:400; font-size:clamp(22px,2.4vw,27px); line-height:1.3;
    margin:0 0 10px; color:var(--ink); }
  .hfa-plotart-actions{ display:flex; flex-wrap:wrap; gap:12px; margin:22px 0 0; }
  .hfa-plotart .btn-primary{ margin-top:0; text-decoration:none; }
  .hfa-plotart .btn-primary:focus-visible{ outline:2px solid var(--accent); outline-offset:3px; }
  .hfa-plotart .dq-note{ margin-top:18px; font-size:14.5px; line-height:1.65; }
  .hfa-future .faq-item.hfa-more{ margin-top:26px; }
  .hfa-future .faq-item.hfa-more + .dq-note{ margin-top:18px; }
  .hfa-jump{ color:var(--accent); text-decoration:none; border-bottom:1px solid rgba(79,107,74,.35); }
  .hfa-jump:hover{ border-bottom-color:var(--accent); }
  .hfa-jump:focus-visible{ outline:2px solid var(--accent); outline-offset:3px; }

  @media(min-width:1000px){ .hfa-band .dq-adv-cols.is-four{ grid-template-columns:repeat(4,minmax(0,1fr)); } }
  @media(max-width:900px){
    .hfa-split, .hfa-split.is-mirror{ grid-template-columns:1fr; }
    .hfa-split.is-mirror .hfa-photo{ order:0; }
    .hfa-split-text.article-section, .hfa-split.is-mirror .hfa-split-text.article-section{ padding:7.5vh 7vw 40px;
      max-width:none; justify-self:stretch; }
  }
  @media(max-width:820px){
    .hfa-checks{ grid-template-columns:1fr; }
    .hfa-band .dq-adv .dq-rows{ grid-template-columns:1fr; gap:16px; }
  }
  @media(max-width:720px){
    .hfa-nav-wrap{ top:12px; margin:24px 0; }
    .hfa-nav{ max-width:calc(100% - 112px); }
    .hfa-nav-list{ padding:0 8px; -webkit-mask-image:linear-gradient(90deg, transparent 0, #000 10px, #000 calc(100% - 14px), transparent 100%);
      mask-image:linear-gradient(90deg, transparent 0, #000 10px, #000 calc(100% - 14px), transparent 100%); }
    .hfa-nav a{ min-height:40px; padding:0 11px; font-size:13px; gap:5px; }
    #open-your-home-to-art, #live-with-art, #discover-and-own, #before-anything-arrives, #discover-your-property,
    #hfa-checks-top{ scroll-margin-top:66px; }
    /* on a phone the split and inset photographs run edge to edge at 4:3 */
    .hfa-photo img{ aspect-ratio:4 / 3; object-fit:cover; }
    .hfa-inset.hfa-photo{ width:100vw; margin:40px 0 44px; border-radius:0; box-shadow:none; }
    .hfa-band .article-section{ padding:60px 0; }
    .hfa-band .article-section + .article-section{ padding-top:44px; }
    .hfa-own .article-section{ padding:48px 0; }
    .hfa-routes .practical-group{ grid-template-columns:1fr; gap:10px; }
    .hfa-routes .practical-item, .hfa-routes .practical-item:first-child{ padding:20px 20px 22px; }
    .faq-item.hfa-more{ padding:0 18px; }
    .hfa-assess{ padding:64px 0 68px; }
    #discover-your-property{ padding:72px 20px 72px; }
    .hfa-check{ padding:24px 20px 24px; }
    .hfa-check .btn-primary, .hfa-plotart-actions .btn-primary{ align-self:stretch; flex:1 1 100%; text-align:center;
      box-sizing:border-box; }
    .hfa-plotart{ padding:24px 20px 26px; }
  }
  @media(prefers-reduced-motion:reduce){ .hfa-nav a{ transition:none; } }
</style>
"""


def artist_public():
    import importlib.util
    spec = importlib.util.spec_from_file_location("artist_register", ROOT / "atlas-tools" / "build-artist-register.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.ARTIST_PUBLIC is True


def plotart():
    """The ONE PlotArt section (founder design decisions, 17 Oct 2026). It keeps
    the TAKE-PART marker build-artist-register.py A11 looks for, and renders only
    while the Artist Register is open. No form here; nothing is matched or arranged."""
    return ('    <!-- PLOTNUA-TAKE-PART · the one PlotArt section: two expressions of interest (founder\n'
            '         decisions 14 and 17 Oct 2026). Shown only while the Artist Register is open. No form\n'
            '         here; nothing is matched or arranged. -->\n'
            '    <aside class="hfa-plotart" aria-labelledby="hfaPlotArtH">\n'
            '      <h3 id="hfaPlotArtH">%s</h3>\n'
            '      <p>%s</p>\n'
            '      <div class="hfa-plotart-actions"><a class="btn-primary" href="%s">%s</a>'
            '<a class="btn-primary" href="%s">%s</a></div>\n'
            '      <p class="dq-note">%s %s</p>\n'
            '    </aside>\n' % (PLOTART_H, PLOTART_P, START24, PLOTART_B1, ARTIST_PAGE, PLOTART_B2,
                               PLOTART_NOTE, PLOTART_HOME_NOTE))


NUMS = ("01", "02", "03")
NAV_ITEMS = (("open-your-home-to-art", "01", "Open"), ("live-with-art", "02", "Live with"),
             ("discover-and-own", "03", "Own"), ("before-anything-arrives", "", "Practical guide"),
             ("discover-your-property", "", "Checks"))
NAV_LABEL = "On this page"
# The in-page navigation (founder decision 2, 17 Oct 2026): a compact sticky pill
# after the empty-wall photograph. It replaces the three chooser cards.
NAV = ('<div class="hfa-nav-wrap">\n'
       '  <nav class="hfa-nav" id="hfaNav" aria-label="%s">\n'
       '    <ul class="hfa-nav-list">\n%s    </ul>\n'
       '  </nav>\n'
       '</div>\n' % (NAV_LABEL, "".join(
           '      <li><a href="#%s">%s%s</a></li>\n' % (a, ('<span class="hfa-nav-n">%s</span> ' % n) if n else "", t)
           for a, n, t in NAV_ITEMS)))
NAV_SCRIPT = """<script>
/* PLOTNUA-HOME-FOR-ART-NAV · marks the section being read in the in-page
   navigation (aria-current="location") and keeps that link in view inside the
   pill on a phone. Reading position only; nothing is stored or sent. */
(function(){
  var nav = document.getElementById('hfaNav');
  if (!nav) return;
  var list = nav.querySelector('.hfa-nav-list');
  var links = [].slice.call(nav.querySelectorAll('a[href^="#"]'));
  var targets = links.map(function(a){ return document.getElementById(a.getAttribute('href').slice(1)); });
  var current = -1, queued = false;
  function update(){
    queued = false;
    var line = window.innerHeight * 0.35, idx = -1;
    for (var i = 0; i < targets.length; i++){
      if (targets[i] && targets[i].getBoundingClientRect().top <= line) idx = i;
    }
    if (idx === current) return;
    current = idx;
    links.forEach(function(a, i){
      if (i === idx) a.setAttribute('aria-current', 'location'); else a.removeAttribute('aria-current');
    });
    if (idx > -1 && list.scrollWidth > list.clientWidth){
      var a = links[idx], l = a.offsetLeft, r = l + a.offsetWidth;
      if (l < list.scrollLeft + 12 || r > list.scrollLeft + list.clientWidth - 12) list.scrollLeft = Math.max(0, l - 24);
    }
  }
  function queue(){ if (!queued){ queued = true; window.requestAnimationFrame(update); } }
  window.addEventListener('scroll', queue, {passive:true});
  window.addEventListener('resize', queue);
  update();
})();
</script>
"""


def _img(plate):
    return re.search(r"<img\b[^>]*>", plate).group(0)


def _cap(plate):
    return re.search(r'<div class="caption"><p>(.*?)</p></div>', plate).group(1)


def photo(plate, cls, note):
    """A split or inset photograph: the source <img> tag verbatim (file, alt,
    dimensions) and the source caption verbatim; only its frame changes."""
    return ('  <figure class="hfa-photo%s">\n'
            '    <!-- %s -->\n'
            '    %s\n'
            '    <figcaption class="hfa-cap"><p>%s</p></figcaption>\n'
            '  </figure>\n' % (cls, note, _img(plate), _cap(plate)))


def expander(sec):
    """A source section folded into a labelled expandable panel: the section's
    own kicker and heading become the label; every word of the body stays in the
    page source (M12 requires moved cautions to sit inside one of these)."""
    m = re.match(r'  <section class="article-section reveal">\n    <div class="kicker">(.*?)</div>\n'
                 r'    <h2>(.*?)</h2>\n', sec)
    if not m:
        die("M12 an expandable section's source no longer opens with a kicker and heading")
    body = sec[m.end():sec.rindex("  </section>")].strip("\n")
    return ('    <details class="faq-item hfa-more">\n'
            '      <summary><h3><span class="hfa-more-k">%s</span>%s</h3><span class="icon"></span></summary>\n'
            '      <div class="hfa-more-body">\n%s\n      </div>\n'
            '    </details>\n' % (m.group(1), m.group(2), body))


def checks_band(hid, hh):
    """The two homeowner checks on deep forest (founder decision 1): the same
    cards and note as the closing assessment band."""
    return ('<section class="hfa-band is-forest hfa-assess" id="%s" aria-labelledby="%s">\n'
            '  <!-- ASSESSMENTS (TOP) · founder decision 1, 17 Oct 2026: straight after the opening and the\n'
            '       SPACE <-> SPACE board. The same two checks are repeated at the foot of the page. -->\n'
            '  <div class="article">\n'
            '    <h2 class="hfa-assess-h" id="%s">%s</h2>\n'
            '    <p class="hfa-assess-intro">%s</p>\n'
            '    <div class="hfa-checks">\n%s%s    </div>\n'
            '    <p class="hfa-assess-note">%s</p>\n'
            '  </div>\n'
            '</section>\n' % (hid, hh, hh, ASSESS_H, ASSESS_INTRO, _card(CARD_HOST, START24),
                              _card(CARD_OWN, START23), ASSESS_NOTE))


def main_html():
    # EDITORIAL REDESIGN (founder approval to build locally, 17 Oct 2026). The
    # hosting story still leads. Order: opening (the overlooked opportunity and
    # SPACE <-> SPACE) -> the two checks on deep forest -> the empty wall
    # (full-bleed) -> the sticky in-page navigation -> 01 Open (split, artist)
    # -> the ladder and "three people" (warm stone) -> the outcome (full-bleed)
    # -> 02 Live with art (sage, inset evening room) -> 03 Discover & own
    # (mirrored split, same wall; the buying detail behind labelled expanders)
    # -> the practical guide (warm stone) -> questions and PlotArt (ivory)
    # -> the closing assessment band (deep forest, outside <main>).
    split_at = O_FIRST.index('    <p class="dq-note"><strong>Nobody has to come to your door.</strong>')
    first_a = O_FIRST[:split_at].rsplit("\n\n", 1)[0] + "\n"     # opening line + SPACE <-> SPACE
    first_b = O_FIRST[split_at:].rsplit("  </section>\n", 1)[0]    # no visitors, the ladder, money
    nobody, ladder = first_b.split("\n", 1)
    if not nobody.endswith("</p>"):
        die("M1 the 'Nobody has to come to your door' sentence moved")
    opening = first_a.replace('  <section class="article-section reveal">\n',
                              '  <section class="article-section reveal hfa-opening">\n'
                              '    <div class="kicker">The overlooked opportunity</div>\n'
                              '    <h2>%s</h2>\n'
                              '    <p class="hfa-lede">%s</p>\n' % (OVERLOOKED_H2, LEDE), 1) + "  </section>\n"
    seller = "<strong>The artist is the seller.</strong> They own the work, set the price, deal with the buyer and receive the payment."
    if seller not in O0:
        die("M1 source sentence moved: the artist is the seller")
    open_split = ('<section class="hfa-split reveal" id="open-your-home-to-art" aria-labelledby="hfaOpenH">\n'
                  '  <div class="hfa-split-text article-section">\n'
                  '    <span class="hfa-num" aria-hidden="true">%s</span>\n'
                  '    <div class="kicker">Possibility one</div>\n'
                  '    <h2 id="hfaOpenH">%s</h2>\n'
                  '    <p class="hfa-branch-lead">%s</p>\n'
                  '%s\n'
                  '  </div>\n%s'
                  '</section>\n' % (NUMS[0], B3[0], B3[1],
                                    nobody.replace('<p class="dq-note">', '<p class="dq-note hfa-pull">', 1),
                                    photo(O_IMG_ARTIST, "",
                                          "THE ARTIST'S PROBLEM, beside Possibility one (split, full frame).")))
    ladder_band = ('<div class="hfa-band is-stone">\n' +
                   art('  <section class="article-section reveal hfa-ladder">\n' + ladder.strip("\n") +
                       "\n  </section>\n", O_BETTER) + '</div>\n')
    routes = "".join('        <li>\n          <span class="dq-adv-label">%s</span>\n'
                     '          <span class="dq-fact">%s</span>\n'
                     '          <span class="dq-note">%s</span>\n        </li>\n' % r for r in LIVE_ROUTES)
    b_live = ('  <section class="article-section reveal" id="live-with-art" aria-labelledby="hfaLiveH">\n'
              '    <span class="hfa-num" aria-hidden="true">%s</span>\n'
              '    <div class="kicker">Possibility two</div>\n'
              '    <h2 id="hfaLiveH">%s</h2>\n'
              '    <p class="hfa-branch-lead">%s</p>\n' % (NUMS[1], B2[0], B2[1]) +
              photo(A_IMG_EVENING, " hfa-inset", "THE EVENING ROOM, inset inside the Live with art band.") +
              '    <h3 class="hfa-live-q">%s</h3>\n' % LIVE_Q +
              '    <p>%s</p>\n' % B2_P1 +
              '    <!-- THE GALLERY COMES TO YOU (founder design decisions, 17 Oct 2026). Three routes a\n'
              '         third party may offer; none is arranged by PlotNua, none is promised, no provider\n'
              '         is named. Replaces the Display tile, which repeated the hosting ladder. -->\n'
              '    <div class="dq-adv">\n      <span class="dq-cat dq-adv-cat">%s</span>\n'
              '      <ul class="dq-adv-cols">\n%s      </ul>\n    </div>\n' % (LIVE_CAT, routes) +
              '    <p><strong>%s</strong> %s</p>\n' % (B2_P2, LIVE_NOT_PLOTNUA) +
              '    <p class="dq-note"><strong>If you come to love the work:</strong> %s</p>\n' % seller.replace(
                  "<strong>The artist is the seller.</strong>", "the artist is the seller.") +
              '    <p class="dq-note"><a class="hfa-jump" href="#before-anything-arrives">Before anything arrives, the custody, insurance '
              'and money questions below apply here too.</a></p>\n' +
              "  </section>\n")
    live_band = '<div class="hfa-band is-sage">\n' + art(b_live) + '</div>\n'
    own_split = ('<section class="hfa-split is-mirror reveal" id="discover-and-own" aria-labelledby="hfaOwnH">\n'
                 '  <div class="hfa-split-text article-section">\n'
                 '    <span class="hfa-num" aria-hidden="true">%s</span>\n'
                 '    <div class="kicker">Possibility three</div>\n'
                 '    <h2 id="hfaOwnH">%s</h2>\n'
                 '    <p class="hfa-branch-lead">%s</p>\n'
                 '  </div>\n%s'
                 '</section>\n' % (NUMS[2], B1[0], B1[1],
                                   photo(A_IMG_SAME, "", "THE SAME WALL, beside Possibility three (mirrored split, full frame).")))
    # "Does it have to be expensive?" and the no-price-guides caution stay on
    # view; the rest of the buying section folds away.
    k = A_BUYING.index('    <div class="planning-sub">Does it have to be expensive?</div>')
    buying = A_BUYING[:k].rstrip() + "\n  </section>\n"
    cost = ('  <section class="article-section reveal hfa-cost">\n' +
            A_BUYING[k:A_BUYING.rindex("  </section>")].rstrip() + "\n  </section>\n")
    look = A_LOOK.replace('<section class="article-section reveal">', '<section class="article-section reveal hfa-routes">', 1)
    more = ('  <section class="article-section reveal hfa-more-group">\n'
            '    <p class="hfa-more-label">%s</p>\n' % MORE_LABEL +
            "".join(expander(s) for s in (buying, A_SIZE, A_COMM, A_BEFORE)) + "  </section>\n")
    own = '<div class="article hfa-own">\n\n' + "\n".join((A_WHY, cost, look, more)) + '\n</div>\n\n'
    settle = O_SETTLE.replace('<section class="article-section reveal">',
                              '<section class="article-section reveal" id="before-anything-arrives">', 1)
    settle_band = '<div class="hfa-band is-stone">\n' + art(settle) + '</div>\n'
    fut_ps = re.findall(r"    <p[^>]*>.*?</p>\n", O_FUTURE, re.S)
    anchor = '    <p class="dq-note">This matching service is not live yet.</p>\n'
    if not fut_ps or fut_ps[-1] != anchor:
        die("M6 the PlotArt section no longer ends with the not-live sentence")
    future = (A_FUTURE.replace('<section class="article-section reveal">', '<section class="article-section reveal hfa-future">', 1)
              .rsplit("  </section>\n", 1)[0] +
              '    <details class="faq-item hfa-more">\n'
              '      <summary><h3>Finding each other</h3><span class="icon"></span></summary>\n'
              '      <div class="hfa-more-body">\n' + "".join(fut_ps[:-1]) + '      </div>\n'
              '    </details>\n' + anchor)
    future += (plotart() if artist_public() else "") + "  </section>\n"
    # IMAGE SPACING: no two photographs ever sit side by side (M12); full-bleed,
    # split and inset alternate. No image is added, removed, regenerated or
    # replaced; every <img> tag is the source's, verbatim (M12).
    return ('<main id="pn-main">\n' +
            art(opening) +
            checks_band("hfa-checks-top", "hfaChecksTopH") +
            O_IMG_PA + "\n" +
            NAV +
            open_split +
            ladder_band +
            O_IMG_OUTCOME + "\n" +
            live_band +
            own_split +
            own +
            settle_band +
            art(A_FAQ, future).rstrip("\n") + "\n</main>\n")


def art(*xs):
    return '<div class="article">\n\n' + "\n".join(xs) + '\n</div>\n\n'


def _card(card, href):
    k, h, line, button = card
    return ('      <div class="hfa-check"><p class="hfa-check-k">%s</p><h3>%s</h3><p>%s</p>\n'
            '        <a class="btn-primary" href="%s">%s</a></div>\n' % (k, h, line, href, button))


# THE ONE ASSESSMENT SECTION (founder design decisions, 17 Oct 2026). Replaces
# the old "Check this against your own home" panel AND every check button that
# was in the branches. Hosting first (M10). Both URLs, with ?start=1, unchanged.
PANEL = ('<section class="pb-preview reveal" id="discover-your-property">\n'
         '    <!-- ONE ASSESSMENT SECTION · TWO INDEPENDENT PROPERTY CHECKS (A Home for Art; founder design\n'
         '         decisions, 17 Oct 2026). Engines, questions, outcomes and My Plot save keys unchanged.\n'
         '         The page\'s only check buttons. No form and no field here. -->\n'
         '    <div class="pn-wordmark">PlotNua</div>\n'
         '    <h2 class="pb-headline">%s</h2>\n'
         '    <p class="pb-subhead">%s</p>\n'
         '    <div class="hfa-checks">\n%s%s'
         '    </div>\n'
         '    <p class="hfa-assess-note">%s</p>\n'
         '    <div class="cs-exits">\n'
         '      <a class="cs-exit" href="discovery-living-in-the-garden.html">Explore What Could You Build in Your Garden? &rarr;</a>\n'
         '      <a class="cs-exit" href="discoveries.html">See all Discoveries &rarr;</a>\n'
         '      <a class="cs-exit is-home" href="index.html">Back to the homepage</a>\n'
         '    </div>\n'
         '  </section>\n' % (ASSESS_H, ASSESS_INTRO, _card(CARD_HOST, START24), _card(CARD_OWN, START23), ASSESS_NOTE))


def related():
    i = once(A0, '<section class="related reveal">', "A related")
    j = A0.index("</section>\n", i) + len("</section>\n")
    rel = A0[i:j]
    k = rel.index('    <a class="related-card" href="discovery-open-your-home-to-art.html">')
    m = rel.index("    </a>\n", k) + len("    </a>\n")
    screen = ('    <a class="related-card" href="discovery-your-home-on-screen.html">\n'
              '      <div class="thumb"><img src="assets/img/ea3f24eedab76294.jpg" loading="lazy" decoding="async" '
              'alt="%s"></div>\n      <div class="r-kicker">On Screen</div>\n      <h3>Your Home on Screen</h3>\n    </a>\n'
              % SCREEN_ALT)
    return rel[:k] + rel[m:].replace("  </div>\n</section>", screen + "  </div>\n</section>", 1), (i, j)


SCREEN_PAGE = (ROOT / "discovery-your-home-on-screen.html").read_text(encoding="utf-8")
SCREEN_ALT = re.search(r'<img id="dHeroImg"[^>]*alt="([^"]*)"', SCREEN_PAGE).group(1)


def merged_page():
    s = A0
    rep = [
        ("<title>How to Buy &amp; Commission Original Irish Art for Your Home | PlotNua</title>", "<title>%s</title>" % TITLE),
        ('content="Choosing original Irish art for your home? Learn where to find local artists, how commissions work, '
         'what to agree and how to choose the right size."', 'content="%s"' % DESC),
        ('<meta property="og:title" content="Buy Original Irish Art | PlotNua Discoveries">',
         '<meta property="og:title" content="%s">' % OG_T),
        ('<meta property="og:description" content="One original work, made by someone you could meet. Where to find local '
         'artists in Ireland, and what to agree before you buy.">', '<meta property="og:description" content="%s">' % OG_D),
        ('<meta name="twitter:title" content="Buy Original Irish Art | PlotNua Discoveries">',
         '<meta name="twitter:title" content="%s">' % OG_T),
        ('<meta name="twitter:description" content="Original art from a local artist, in an ordinary Irish home. Where to '
         'look, how to get the size right, and what to agree before buying.">',
         '<meta name="twitter:description" content="%s">' % OG_D),
        ("    <h1>Buy Original Irish Art</h1>\n    <p class=\"subtitle\">One original work, made by someone you could meet.</p>\n"
         "    <p class=\"intro\">You may already have the place for something original.</p>",
         "    <h1>A Home for Art</h1>\n    <p class=\"subtitle\">%s</p>\n    <p class=\"intro\">%s</p>" % (HERO_SUB, HERO_INTRO)),
        ("  <p>What if the wall you stopped noticing became the part of the room you noticed first?</p>",
         "  <p>What if a room you rarely use could give local art somewhere to be seen?</p>"),
        ("  /* ---- DOMINANT OPPORTUNITY SURFACE (property-revelation pilot).",
         PORTED_CSS + "  /* ---- DOMINANT OPPORTUNITY SURFACE (property-revelation pilot)."),
        ('<a href="discovery-open-your-home-to-art.html" style="display:inline-block;padding:10px 14px;border:1px solid '
         'rgba(31,68,53,.24);border-radius:999px;color:#214635;text-decoration:none;font-family:Arial,sans-serif;'
         'font-size:.92rem;">Could your home give art somewhere to be seen? →</a>', ""),
    ]
    rep.append((BUY_HERO_TAG, HOST_HERO_TAG))
    for old, new in rep:
        once(s, old, "A head/hero")
        s = s.replace(old, new)
    # the cross-link style block is retired with the cross-links
    s = re.sub(r"\n<style>/\* PLOTNUA-ART-XLINK-STYLE[\s\S]*?</style>", "", s)
    s = s.replace("</head>", MERGE_CSS + "</head>", 1)
    i = once(s, '<main id="pn-main">', "A main")
    j = s.index("</main>\n", i) + len("</main>\n")
    s = s[:i] + main_html() + s[j:]
    i = once(s, '<section class="pb-preview reveal" id="discover-your-property">', "A panel")
    j = s.index("  </section>\n", i) + len("  </section>\n")
    s = s[:i] + PANEL + s[j:]
    rel, _ = related()
    i = once(s, '<section class="related reveal">', "A related (merged)")
    j = s.index("</section>\n", i) + len("</section>\n")
    s = s[:i] + rel + s[j:]
    once(s, "</body>", "A body end")
    s = s.replace("</body>", NAV_SCRIPT + "</body>", 1)
    # FACTUAL CORRECTIONS (17 Oct 2026): each source sentence exactly once.
    for old, new in CORRECTIONS:
        once(s, old, "correction")
        s = s.replace(old, new)
    return s


REDIRECT = """<!DOCTYPE html>
<html lang="en-IE">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>A Home for Art | PlotNua</title>
<!-- REDIRECT, NOT A DISCOVERY. Open Your Home to Art is now the third branch of
     A Home for Art (founder decision, 13 Oct 2026). GitHub Pages cannot send a
     server-side redirect, so this page does it in the browser: the script keeps
     any query string (for example a social-media click id) and lands on the
     hosting branch; the noscript refresh covers browsers without script.
     Generated by atlas-tools/build-a-home-for-art-merge.py. Not in the sitemap. -->
<link rel="canonical" href="https://plotnua.ie/discovery-a-home-for-art.html">
<script>
(function () {
  var known = ['#discover-and-own', '#live-with-art', '#open-your-home-to-art', '#before-anything-arrives'];
  var hash = known.indexOf(location.hash) > -1 ? location.hash : '#open-your-home-to-art';
  location.replace('discovery-a-home-for-art.html' + location.search + hash);
})();
</script>
<noscript><meta http-equiv="refresh" content="0; url=discovery-a-home-for-art.html#open-your-home-to-art"></noscript>
<style>body{font-family:'Work Sans',system-ui,sans-serif;background:#F8F5EC;color:#1F3B2E;margin:0;padding:12vh 7vw;line-height:1.6;}
a{color:#4F6B4A;}</style>
</head>
<body>
<p>Open Your Home to Art is now part of <a href="discovery-a-home-for-art.html#open-your-home-to-art">A Home for Art</a>.</p>
</body>
</html>
"""

# ---------------------------------------------------- consolidation edits --
MERGED_LINE = "Your home could be more than somewhere to hang art."
CONSOLIDATION = [
    ("index.html",
     '      <a class="d-card" href="discovery-open-your-home-to-art.html">\n'
     '        <div class="d-card-media"><img src="assets/img/dfb125ba9dd7cd87.jpg" loading="lazy" decoding="async" alt="A generous Irish living room hung with large, bold contemporary canvases, with visitors talking and looking at the work."></div>\n'
     '        <div class="d-card-copy">\n'
     '          <h3>Open Your Home to Art</h3>\n'
     '          <p>Store, display or help local art find a buyer &mdash; at a level you choose.</p>\n'
     '        </div>\n'
     '      </a>\n', ""),
    ("index.html", "          <h3>Buy Original Irish Art</h3>\n          <p>Discover and buy original artwork from artists across Ireland.</p>",
     "          <h3>A Home for Art</h3>\n          <p>%s</p>" % MERGED_LINE),
    ("404.html",
     '      <a class="d-card" href="discovery-open-your-home-to-art.html">\n'
     '        <div class="d-card-media"><img src="assets/img/dfb125ba9dd7cd87.jpg" loading="lazy" decoding="async" alt="A generous Irish living room hung with large, bold contemporary canvases, with visitors talking and looking at the work."></div>\n'
     '        <div class="d-card-copy">\n'
     '          <div class="d-tag">Share something</div>\n'
     '          <h3>Open Your Home to Art</h3>\n'
     '          <p>Store, display or help local art find a buyer &mdash; at a level you choose.</p>\n'
     '        </div>\n'
     '      </a>\n', ""),
    ("404.html", "          <h3>Buy Original Irish Art</h3>\n          <p>Discover and buy original artwork from artists across Ireland.</p>",
     "          <h3>A Home for Art</h3>\n          <p>%s</p>" % MERGED_LINE),
    ("discoveries.html",
     '      <a class="lib-card" href="discovery-open-your-home-to-art.html" data-cat="Art">\n'
     '        <span class="lib-shot"><img src="assets/img/dfb125ba9dd7cd87.jpg" alt="A living room with exposed timber beams, hung with large contemporary canvases, with half a dozen visitors talking and looking at the work." loading="lazy" decoding="async" width="800" height="600"></span>\n'
     '        <span class="lib-meta">\n'
     '          <span class="lib-cat">Art</span>\n'
     '        <span class="lib-live">Property check live</span>\n'
     '        </span>\n'
     '        <span class="lib-title">Open Your Home to Art</span>\n'
     '        <span class="lib-line">Store, display or help local art find a buyer &mdash; at a level you choose.</span>\n'
     '      </a>\n', ""),
    ("discoveries.html", '        <span class="lib-title">Buy Original Irish Art</span>\n'
     '        <span class="lib-line">Discover and buy original artwork from artists across Ireland.</span>',
     '        <span class="lib-title">A Home for Art</span>\n        <span class="lib-line">%s</span>' % MERGED_LINE),
    ("atlas-tools/discovery-library-images.json",
     '    {\n      "title": "Open Your Home to Art",\n      "card": "discovery-open-your-home-to-art.html",\n'
     '      "image": "assets/img/dfb125ba9dd7cd87.jpg",\n'
     '      "alt": "A living room with exposed timber beams, hung with large contemporary canvases, with half a dozen visitors talking and looking at the work.",\n'
     '      "why": "The home open and the art being seen by people. The selector rule chose 046ec577a454599b, the same room with its large wall empty and annotated as a potential asset.",\n'
     '      "previous": "assets/img/dfb125ba9dd7cd87.jpg"\n    },\n', ""),
    ("atlas-tools/discovery-library-images.json", '"title": "Buy Original Irish Art",\n      "card": "discovery-a-home-for-art.html"',
     '"title": "A Home for Art",\n      "card": "discovery-a-home-for-art.html"'),
    ("discovery-living-in-the-garden.html",
     '    <a class="related-card" href="discovery-open-your-home-to-art.html">\n'
     '      <div class="thumb"><img src="assets/img/dfb125ba9dd7cd87.jpg" loading="lazy" decoding="async" alt="A generous Irish living room hung with large, bold contemporary canvases, with visitors talking and looking at the work."></div>\n'
     '      <div class="r-kicker">Sharing Your Space</div>\n'
     '      <h3>Open Your Home to Art</h3>\n'
     '    </a>\n', ""),
    ("discovery-living-in-the-garden.html",
     '      <div class="r-kicker">Original Art</div>\n      <h3>Buy Original Irish Art</h3>',
     '      <div class="r-kicker">Original Art</div>\n      <h3>A Home for Art</h3>'),
    ("discovery-your-home-on-screen.html",
     '    <a class="related-card" href="discovery-open-your-home-to-art.html">',
     '    <a class="related-card" href="%s">' % TARGET),
    ("discovery-your-home-on-screen.html",
     '      <span class="related-title">Open Your Home to Art</span>',
     '      <span class="related-title">A Home for Art</span>'),
    ("your-plot.html", "    'disc024-open-your-home-to-art': 'discovery-open-your-home-to-art.html',",
     "    'disc024-open-your-home-to-art': '%s'," % TARGET),
    (C24, '    <a class="ho-back" href="discovery-open-your-home-to-art.html">Back to the story</a>',
     # 14 Oct 2026: on the intro the control is now labelled "Explore A Home for
     # Art" (two-option entry, governed by build-art-space-register.py E4).
     '    <a class="ho-back" id="hoBack" href="%s" aria-label="Explore A Home for Art">' % TARGET),
    ("sitemap.xml", "  <url><loc>https://plotnua.ie/discovery-open-your-home-to-art.html</loc><lastmod>2026-08-27</lastmod>"
     "<changefreq>monthly</changefreq><priority>0.8</priority></url>\n", ""),
    # The merge's lastmod edit for this page (2026-08-27 -> 2026-10-13) is no
    # longer a byte pair: see SITEMAP_PAGE below (M9 re-baseline, 17 Oct 2026).
    ("atlas-tools/build-search-index.py",
     '    "disc024-open-your-home-to-art.html": "discovery-open-your-home-to-art.html",',
     '    # DISC-024 consolidated into DISC-023 at the Discovery-page level (13 Oct 2026):\n'
     '    # the check is unchanged and now routes onward to A Home for Art.\n'
     '    "disc024-open-your-home-to-art.html": "discovery-a-home-for-art.html",'),
    ("atlas-tools/prove-landmarks.mjs",
     '  "discovery-living-in-the-garden.html", "discovery-a-home-for-art.html",\n'
     '  "discovery-open-your-home-to-art.html", "discovery-the-borrowed-garden.html",',
     '  "discovery-living-in-the-garden.html", "discovery-a-home-for-art.html",\n'
     '  // discovery-open-your-home-to-art.html is now a redirect to A Home for Art (13 Oct 2026)\n'
     '  "discovery-the-borrowed-garden.html",'),
    ("atlas-tools/prove-landmarks.mjs", "// ---- L2 · all 13 public Discoveries", "// ---- L2 · all 12 public Discoveries"),
    ("atlas-tools/prove-landmarks.mjs", 'bad("L2 all 13 public Discoveries have one main"',
     'bad("L2 all 12 public Discoveries have one main"'),
    ("atlas-tools/prove-landmarks.mjs", 'ok("L2 all 13 public Discoveries have exactly one main landmark")',
     'ok("L2 all 12 public Discoveries have exactly one main landmark")'),
]
CONSOLIDATION += [
    # M9 RE-BASELINE (17 Oct 2026). The merge's own contribution here is the
    # recorded reduction (the redirect left the rail scope). The count itself is
    # owned by build-search-rail.py and rose to 22 again with the Garden Room
    # Prices guide (SEO Phase 2), so the pair is anchored on the triq-cube note
    # that precedes the merge's comment, not on the number.
    ("atlas-tools/build-search-rail.py",
     "# stub, so a re-run of this builder reproduces it rather than changing it.\nEXPECTED_PAGES = 22\n",
     "# stub, so a re-run of this builder reproduces it rather than changing it.\n"
     "# 21 since 13 October 2026: discovery-open-your-home-to-art.html became a\n"
     "# redirect to A Home for Art and left the sitemap (founder decision).\n"),
    ("atlas-tools/prove-discovery-library-capability.py", '("Buy Original Irish Art", "discovery-a-home-for-art.html",',
     '("A Home for Art", "discovery-a-home-for-art.html",'),
]
# IMAGE CORRECTION (13 Oct 2026): every card that represents A Home for Art shows
# the hosting Discovery's hero, with the alt text that card slot already used for it.
HOST_CARD_ALT = ("A generous Irish living room hung with large, bold contemporary canvases, with visitors talking "
                 "and looking at the work.")
BUY_CARD = ('<img src="assets/img/c0f5bfcde033dea3.jpg" loading="lazy" decoding="async" alt="A calm Irish living room '
            'with a timber ceiling and a wide sea view, and one large original painting hanging above the fireplace.">')
HOST_CARD = '<img src="assets/img/dfb125ba9dd7cd87.jpg" loading="lazy" decoding="async" alt="%s">' % HOST_CARD_ALT
CONSOLIDATION += [
    ("index.html", '        <div class="d-card-media">%s</div>\n        <div class="d-card-copy">\n          <h3>A Home for Art</h3>' % BUY_CARD,
     '        <div class="d-card-media">%s</div>\n        <div class="d-card-copy">\n          <h3>A Home for Art</h3>' % HOST_CARD),
    ("404.html", '        <div class="d-card-media">%s</div>\n' % BUY_CARD, '        <div class="d-card-media">%s</div>\n' % HOST_CARD),
    ("discovery-living-in-the-garden.html",
     '      <div class="thumb"><img src="assets/img/c0f5bfcde033dea3.jpg" loading="lazy" decoding="async" alt="A calm Irish '
     'living room with a timber ceiling and a wide sea view, and one large original painting of a coastline hanging above the fireplace."></div>',
     '      <div class="thumb">%s</div>' % HOST_CARD),
    ("your-plot.html",
     "      img: 'assets/img/c0f5bfcde033dea3.jpg',\n"
     "      alt: 'A calm Irish living room with a timber ceiling and one large painting on the wall.',",
     "      img: 'assets/img/dfb125ba9dd7cd87.jpg',\n"
     "      alt: 'An Irish living room hung with large contemporary canvases, half a dozen visitors talking and looking at the work, the sofa and rug still in place.',"),
    ("atlas-tools/discovery-library-images.json",
     '      "image": "assets/img/c1d46445b6a79373.jpg",\n'
     '      "alt": "An Irish living room with a large original landscape painting hung above the fireplace and flowers on the table.",\n'
     '      "why": "The artwork bought and hung. The selector rule chose 5dc201bef1868b84 -- the same room with the wall above the fireplace empty, annotated as a potential asset.",\n'
     '      "previous": "assets/img/c0f5bfcde033dea3.jpg"',
     '      "image": "assets/img/dfb125ba9dd7cd87.jpg",\n'
     '      "alt": "A living room with exposed timber beams, hung with large contemporary canvases, with half a dozen visitors talking and looking at the work.",\n'
     '      "why": "Founder image correction, 13 Oct 2026: A Home for Art leads with Open Your Home to Art, so the card shows that Discovery\'s own hero -- the home open and the art being seen by people -- not the buyer room.",\n'
     '      "previous": "assets/img/c1d46445b6a79373.jpg"'),
]
# your-plot.html · Hidden Potential: one entry for the merged Discovery.
YP = (ROOT / "your-plot.html").read_text(encoding="utf-8")
m = re.search(r"    \{ name: 'Open Your Home to Art', category: 'home-use', href: 'discovery-open-your-home-to-art\.html'.*?\},\n", YP, re.S)
if m:
    CONSOLIDATION.append(("your-plot.html", m.group(0), ""))
CONSOLIDATION.append(("your-plot.html", "{ name: 'Buy Original Irish Art', category: 'art', href: 'discovery-a-home-for-art.html'",
                      "{ name: 'A Home for Art', category: 'art', href: 'discovery-a-home-for-art.html'"))


REGISTER_BLOCKS = (("/* PLOTNUA-ART-REGISTER-CSS-BEGIN", "/* PLOTNUA-ART-REGISTER-CSS-END */\n"),
                   ("    <!-- PLOTNUA-ART-REGISTER-HTML-BEGIN", "    <!-- PLOTNUA-ART-REGISTER-HTML-END -->\n"),
                   ("    /* PLOTNUA-ART-REGISTER-CALL-BEGIN", "    /* PLOTNUA-ART-REGISTER-CALL-END */\n"),
                   ("<script>\n/* PLOTNUA-ART-REGISTER-JS-BEGIN", "/* PLOTNUA-ART-REGISTER-JS-END */\n</script>\n"))


# FOUNDER-APPROVED DISC-024 CHECK WORDING. 13 Oct 2026 (21:30): the storage
# option no longer suggests attics, garages or under-stairs spaces. 14 Oct 2026:
# the space-conditions question and its three options. Text only: the answer
# values below them, the engine, outcomes and save keys are pinned to BASE (M8).
CHECK24_APPROVED = [
    "{v:'dry_store',      l:'Storage only', n:'Subject to suitability'},",
    "'space_store':          'You might have space suitable for storing finished artwork, subject to the "
    "artist&rsquo;s requirements.',",
    "q:'What are the conditions like in the space you&rsquo;re considering?',",
    "{v:'dry_stable',         l:'Dry and sheltered', n:null},",
    "{v:'not_dry_or_sunny',   l:'Some dampness or exposure &mdash; the space might need improvements', n:null},",
    "{v:'not_sure_condition', l:'I&rsquo;m not sure &mdash; I&rsquo;d need to check', n:null}]},",
]


# DISC-023 CHECK WORDING (founder design decisions, 17 Oct 2026). Result copy
# only, two strings in ACTIONS: the dated Culture Night sentence (18 September
# 2026 had passed) and the RHA / RDS seasons, matched to the Discovery's
# corrected wording. The engine, questions, answer values, outcome selection,
# save keys and every other byte stay pinned to BASE: M8 reverts exactly these
# pairs (and the two-option entry) before comparing the page with BASE.
# Applied by --apply through CONSOLIDATION (M9). Kept in its own commit so the
# founder can take or drop it independently of the Discovery changes.
CHECK23_WORDING = [
    ("      'Go and stand in front of a lot of real work before you buy any of it. ' +\n"
     "      'The RHA Annual Exhibition runs free through the summer with everything ' +\n"
     "      'in it for sale. Art Source fills the RDS each November. The RDS Visual ' +\n"
     "      'Art Awards show graduate work each winter.',\n",
     "      'Go and stand in front of a lot of real work before you buy any of it. ' +\n"
     "      'The RHA Annual Exhibition runs free from late spring through the ' +\n"
     "      'summer, with almost everything in it for sale. Art Source fills the ' +\n"
     "      'RDS each November. The RDS Visual Art Awards exhibition opens each ' +\n"
     "      'November, showing emerging artists chosen from graduate shows.',\n"),
    ("      'Culture Night is the evening built for exactly this — Friday 18 ' +\n"
     "      'September 2026, free, nationwide, coordinated through local authority ' +\n"
     "      'arts offices, with open studios an invited event type. More than 1,800 ' +\n"
     "      'events ran in 2025. Artists open their working spaces at other times ' +\n"
     "      'too, and you can usually buy on the spot.',\n",
     "      'Culture Night is the evening built for exactly this — every ' +\n"
     "      'September, free, nationwide, coordinated by the Arts Council with ' +\n"
     "      'local authorities, with open studios an invited event type. Artists ' +\n"
     "      'open their working spaces at other times too, and you can usually ' +\n"
     "      'buy on the spot.',\n"),
]
CONSOLIDATION += [(C23, old, new) for old, new in CHECK23_WORDING]


def check24_head(t):
    return t[:t.index("<style>")]


def check24_engine(t):
    blocks = [x for x in re.findall(r"<script>[\s\S]*?</script>", t) if "root.PlotNuaHostEngine = {" in x]
    if len(blocks) != 1:
        raise ValueError("engine")
    return blocks[0]


def check24_save(t):
    return re.search(r"/\* PLOTNUA-JOURNEY-SAVE-BEGIN \*/[\s\S]*?/\* PLOTNUA-JOURNEY-SAVE-END \*/", t).group(0)


def check24_values(t):
    q = re.search(r"var QUESTIONS = \[([\s\S]*?)\n  \];", t).group(1)
    return re.findall(r"\{var:'(\w+)'|\{v:'(\w+)'", q)


def check24_savecall(t):
    m = re.search(r"journeyId: '([^']+)',[\s\S]*?return (\{ answers: answers, resultKeys: \{ host_state: r\.state \} \});", t)
    return (m.group(1), m.group(2))


def art_entry():
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "art_space_register", ROOT / "atlas-tools" / "build-art-space-register.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def strip_register(html):
    for b, e in REGISTER_BLOCKS:
        if html.count(b) != 1 or html.count(e) != 1:
            die("M8 the Art Space Register blocks on the DISC-024 check are not intact")
        html = re.sub(re.escape(b) + r"[\s\S]*?" + re.escape(e), "", html)
    return html


# M9 RE-BASELINE (founder instruction, 17 Oct 2026). The merge moved this page's
# sitemap lastmod from the pre-merge 2026-08-27 to 2026-10-13. The date itself
# is not this builder's to pin: build-artist-register.py later moved it to
# 2026-10-14 and 808c26f recomputed every lastmod from full git history, which
# made the old byte pair unfindable and the builder refuse at HEAD. M9 now holds
# only what the merge owns: the page is listed exactly once and no longer
# carries its pre-merge date. Whatever owns lastmod may move it forward.
SITEMAP_PAGE = "<loc>https://plotnua.ie/discovery-a-home-for-art.html</loc><lastmod>"
SITEMAP_PRE_MERGE = SITEMAP_PAGE + "2026-08-27</lastmod>"


def sitemap_lastmod(write):
    p = ROOT / "sitemap.xml"
    t = p.read_text(encoding="utf-8")
    if t.count(SITEMAP_PAGE) != 1:
        die("M9 the sitemap does not list A Home for Art exactly once")
    if SITEMAP_PRE_MERGE in t:
        if not write:
            die("M9 consolidation edit not applied in sitemap.xml: the pre-merge lastmod is still present")
        p.write_text(t.replace(SITEMAP_PRE_MERGE, SITEMAP_PAGE + "2026-10-13</lastmod>"), encoding="utf-8")


def apply_edits(write):
    sitemap_lastmod(write)
    for f, old, new in CONSOLIDATION:
        p = ROOT / f
        t = p.read_text(encoding="utf-8")
        done = (new != "" and t.count(new) >= 1 and old not in t) or (new == "" and old not in t)
        if done:
            continue
        if t.count(old) != 1:
            die("M9 consolidation edit not found exactly once in %s: %s" % (f, " ".join(old.split())[:70]))
        if write:
            p.write_text(t.replace(old, new), encoding="utf-8")
        else:
            die("M9 consolidation edit not applied in %s: %s" % (f, " ".join(old.split())[:70]))


def text_blocks(fragment):
    f = re.sub(r"<!--[\s\S]*?-->", " ", fragment)
    f = re.sub(r"<(script|style)[\s\S]*?</\1>", " ", f)
    out = []
    for tag in ("p", "li", "h1", "h2", "h3", "summary", "span", "div", "a", "strong"):
        for inner in re.findall(r"<%s\b[^>]*>(.*?)</%s>" % (tag, tag), f, re.S):
            if "<%s" % tag in inner:
                continue
            t = re.sub(r"<[^>]+>", " ", inner)
            t = re.sub(r"\s+", " ", htmllib.unescape(t)).strip()
            if t:
                out.append(t)
    return out


def norm(s):
    return re.sub(r"\s+", " ", htmllib.unescape(re.sub(r"<[^>]+>", " ", re.sub(r"<!--[\s\S]*?-->", " ", s)))).strip()


def guards(page):
    i = page.index('<header class="d-hero">')
    j = page.index("<!-- Discovery SEO V1")
    body = page[i:j]
    src = (norm(A0) + " " + norm(O0) + " " + norm(SCREEN_PAGE)).lower()
    approved = sorted((norm(x).lower() for x in NEW_TEXT), key=len, reverse=True)
    for t in text_blocks(body):
        rest = t.lower()
        for a in approved:
            rest = rest.replace(a, "\x00")
        for seg in rest.split("\x00"):
            seg = seg.strip(" .:;,—→↔-")
            if seg and seg not in src:
                die("M1 untraceable text on the merged page: %r" % seg[:90])
    for a in ("discover-and-own", "live-with-art", "open-your-home-to-art", "before-anything-arrives"):
        if page.count('id="%s"' % a) != 1:
            die("M2 anchor #%s not present exactly once" % a)
    # M3 (amended twice on 17 Oct 2026). Founder design decisions: each check
    # offered in one assessment section. EDITORIAL REDESIGN (founder decision 1):
    # TWO placements of that same section, one straight after the opening and one
    # at the foot of the page, each with exactly one hosting card then one buying
    # card. The only other route to the DISC-024 check is the PlotArt section's
    # homeowner button (it starts the check whose result offers the Art Space
    # Register). The DISC-023 check has no other link.
    def placement(start):
        pi = page.index(start)
        return page[pi:page.index("</section>\n", pi)]
    for name, start in (("top", '<section class="hfa-band is-forest hfa-assess" id="hfa-checks-top"'),
                        ("closing", '<section class="pb-preview reveal" id="discover-your-property">')):
        if page.count(start) != 1:
            die("M3 the %s assessment section is missing or repeated" % name)
        panel = placement(start)
        if panel.count('href="%s"' % START24) != 1 or panel.count('href="%s"' % START23) != 1 \
                or panel.index('href="%s"' % START24) > panel.index('href="%s"' % START23) \
                or panel.count('<div class="hfa-check">') != 2:
            die("M3 the %s assessment section must offer each check exactly once, hosting first" % name)
    ti = page.find("<!-- PLOTNUA-TAKE-PART")
    pa = page[ti:page.index("</aside>", ti)] if ti > -1 else ""
    if page.count('href="%s"' % START23) != 2 or \
            page.count('href="%s"' % START24) != 2 + pa.count('href="%s"' % START24) or pa.count('href="%s"' % START24) > 1:
        die("M3 a Property Check is linked outside the two assessment sections (other than PlotArt's homeowner button)")
    if page.count('href="%s"' % C23) or page.count('href="%s"' % C24):
        die("M3 a Property Check is linked without ?start=1")
    if 'href="%s"' % OLD in page:
        die("M3 the merged page links to the old URL")
    vis = norm(body).lower()
    bad = re.search(r"plotnua (will|can) (arrange|place|lend|match|introduce|book)|book a (viewing|placement)|"
                    r"loan service|rental service|matching service is (live|available)|guarantee", vis)
    if bad:
        die("M4 service claim: %r" % bad.group(0))
    allowed_imgs = set(re.findall(r'assets/img/[0-9a-f]{16}\.jpg', A0 + O0)) | {"assets/img/ea3f24eedab76294.jpg"}
    for img in re.findall(r'assets/img/[0-9a-f]{16}\.jpg', page):
        if img not in allowed_imgs:
            die("M5 image not published on either source page: " + img)
        if not (ROOT / img).exists():
            die("M5 image file missing: " + img)
    for must in ("Allianz lists visitors&rsquo; property", "Rent-a-Room Relief does not apply",
                 "A Section 5 declaration gives a formal answer", "It is the artist&rsquo;s relief, never the host&rsquo;s.",
                 "Copyright stays with the artist.", "Household policies often cap individual items.",
                 "This matching service is not live yet.", "PlotArt is in development as a sister site to PlotNua",
                 "PlotNua does not publish price guides.", "PlotNua does not value or authenticate work.",
                 B2_P1, B2_P2):
        if must not in page:
            die("M6 caution or approved sentence missing: " + must[:60])
    red = (ROOT / OLD).read_text(encoding="utf-8")
    if red != REDIRECT or "<main" in red or 'rel="canonical" href="https://plotnua.ie/discovery-a-home-for-art.html"' not in red \
            or "location.search" not in red or "#open-your-home-to-art" not in red:
        die("M7 redirect page is not the governed redirect")
    if OLD in (ROOT / "sitemap.xml").read_text(encoding="utf-8"):
        die("M7 the redirect page is still in the sitemap")
    # The Art Space Register's own four marked blocks on the DISC-024 check are
    # governed by atlas-tools/build-art-space-register.py (R1-R14), which proves
    # the rest of that page byte-identical. M8 compares everything else.
    head24, cur24 = base(C24), (ROOT / C24).read_text(encoding="utf-8")
    strip_register(cur24)                       # the register's four blocks must be intact
    for label, fn in (("head scripts", check24_head), ("engine script", check24_engine),
                      ("My Plot save script", check24_save), ("question variables and answer values", check24_values),
                      ("save call (journeyId and payload)", check24_savecall)):
        try:
            same = fn(head24) == fn(cur24)
        except (AttributeError, ValueError, IndexError):
            same = False
        if not same:
            die("M8 the DISC-024 check's %s differ from BASE" % label)
    if ('id="hoBack" href="%s"' % TARGET) not in cur24 or OLD in cur24:
        die("M8 the DISC-024 Back control does not route to the merged page")
    for phrase in CHECK24_APPROVED:
        if cur24.count(phrase) != 1:
            die("M8 founder-approved DISC-024 wording missing: " + phrase[:60])
    # M10 · founder hierarchy: hosting story first, then Open > Live with > Discover & own; hosting check first
    # Amended 17 Oct 2026 (EDITORIAL REDESIGN, founder decisions 1 and 2): the
    # opening, then the top assessment band, then the empty wall, then the
    # in-page navigation (which replaces the three chooser cards); 01 opens on the
    # artist photograph, 02 carries the evening room, 03 the same wall; the
    # practical guide and PlotArt follow, and the closing assessment band is last.
    order = [page.find(x) for x in (HOST_HERO_TAG, "<h2>%s</h2>" % OVERLOOKED_H2, 'id="hfa-checks-top"',
                                     "assets/img/046ec577a454599b.jpg", 'class="hfa-nav"', 'id="open-your-home-to-art"',
                                     "assets/img/6442d19ec2dd1df0.jpg", "assets/img/05cab54ac0af83d0.jpg",
                                     'id="live-with-art"', "assets/img/571594a8d5b2e80a.jpg", 'id="discover-and-own"',
                                     "assets/img/c1d46445b6a79373.jpg", 'id="before-anything-arrives"') +
             ((("<!-- PLOTNUA-TAKE-PART",) if artist_public() else ()) +
              ("</main>", 'id="discover-your-property"'))]
    if -1 in order or order != sorted(order):
        die("M10 the founder's visual and narrative hierarchy is not in order: %r" % order)
    # M11 · original hosting imagery leads, and every card for this Discovery shows it
    if page.count(HOST_HERO_TAG) != 1 or page.count(HOST_HERO) != 1:
        die("M11 the hero is not the original Open Your Home to Art hero (exactly once)")
    if BUY_HERO in page:
        die("M11 the buyer hero c0f5bf is back on the merged page")
    hosting_seq = [page.find(x) for x in (HOST_HERO, "assets/img/046ec577a454599b.jpg",
                                           "assets/img/6442d19ec2dd1df0.jpg", "assets/img/05cab54ac0af83d0.jpg")]
    buyer_imgs = [page.find(x) for x in ("assets/img/571594a8d5b2e80a.jpg", "assets/img/c1d46445b6a79373.jpg")]
    if -1 in hosting_seq + buyer_imgs or hosting_seq != sorted(hosting_seq) or \
            page.find('id="discover-and-own"') > page.find("assets/img/c1d46445b6a79373.jpg"):
        die("M11 the hosting image sequence or the buyer image placement is wrong: %r %r" % (hosting_seq, buyer_imgs))
    for f, pat in (("index.html", r'<a class="d-card" href="%s">\s*<div class="d-card-media"><img src="([^"]+)"'),
                   ("404.html", r'<a class="d-card" href="%s">\s*<div class="d-card-media"><img src="([^"]+)"'),
                   ("discoveries.html", r'<a class="lib-card" href="%s"[^>]*>\s*<span class="lib-shot"><img src="([^"]+)"'),
                   ("discovery-living-in-the-garden.html", r'<a class="related-card" href="%s">\s*<div class="thumb"><img src="([^"]+)"'),
                   ("your-plot.html", r"href: '%s', built: true,[\s\S]*?img: '([^']+)'")):
        cards = re.findall(pat % re.escape(MERGED), (ROOT / f).read_text(encoding="utf-8"))
        if len(cards) != 1 or cards[0] != HOST_HERO:
            die("M11 the %s card for A Home for Art does not show the hosting image: %r" % (f, cards))
    stale = [f.name for f in ROOT.glob("*.html") if f.name != OLD and
             re.search(r"""href=["']%s["']|'%s'""" % (re.escape(OLD), re.escape(OLD)), f.read_text(encoding="utf-8"))]
    if stale:
        die("M9 live pages still link to the old URL: " + ", ".join(sorted(stale)))
    # The two-option entry (14 Oct 2026) is the only permitted change to the
    # DISC-023 check; it is reverted with the art builder's own pairs first.
    head23 = base(C23)
    cur23 = (ROOT / C23).read_text(encoding="utf-8")
    for old, new in CHECK23_WORDING:        # amended 17 Oct 2026: declared result wording
        if cur23.count(new) != 1:
            die("M8 founder-approved DISC-023 result wording missing: " + " ".join(new.split())[:60])
        cur23 = cur23.replace(new, old)
    if art_entry().entry_revert(C23, cur23) != head23:
        die("M8 the DISC-023 check changed beyond the two-option entry and the declared result wording")
    m12(page)


def m12(page):
    """M12 · FOUNDER DESIGN DECISIONS (17 Oct 2026): the consolidation holds.
    Two plates never sit side by side; the retired check buttons, descriptions
    and the top-of-page invitation do not come back; PlotArt is invited once;
    Live with art carries its three routes and no Display tile."""
    shown = re.sub(r"<!--[\s\S]*?-->", "", page)
    plates = [m.start() for m in re.finditer(r'<section class="imagine-photo', shown)]
    for a, b in zip(plates, plates[1:]):
        if '<div class="article">' not in shown[a:b]:
            die("M12 two full-bleed images sit side by side with no content between them")
    for gone in RETIRED:
        if gone in page:
            die("M12 retired element is back: " + gone[:60])
    if artist_public():
        if page.count("<!-- PLOTNUA-TAKE-PART") != 1 or page.count('href="%s"' % ARTIST_PAGE) != 1:
            die("M12 the PlotArt registers must be invited exactly once")
    li = page.index('id="live-with-art"')
    live = page[li:page.index("  </section>\n", li)]
    if 'dq-adv-label">Display<' in live or "<h3 class=\"hfa-live-q\">%s</h3>" % LIVE_Q not in live or \
            any(r[0] not in live for r in LIVE_ROUTES) or LIVE_NOT_PLOTNUA not in live:
        die("M12 Live with art does not carry the gallery-comes-to-you routes, or still repeats the Display tile")
    for _, new in CORRECTIONS:
        if page.count(new) != 1:
            die("M12 factual correction not present exactly once: " + new[:60])
    m12_redesign(page, shown)


# Cautions that must stay on view at headline level (founder approval, 17 Oct
# 2026: "every caution stays visible at headline level"), and the cautions the
# redesign moved behind a labelled expander.
VISIBLE_CAUTIONS = ("Do not assume a home policy protects somebody else&rsquo;s artwork.",
                    "If money changes hands, it is income.", B2_P2, "the artist is the seller.",
                    "PlotNua does not publish price guides.", "This matching service is not live yet.",
                    "Nobody has to come to your door.")
FOLDED_CAUTIONS = ("Household policies often cap individual items.", "Copyright stays with the artist.",
                   "Allianz lists visitors&rsquo; property", "It is the artist&rsquo;s relief, never the host&rsquo;s.",
                   "PlotNua does not value or authenticate work.")
PHOTOS = (HOST_HERO_TAG.strip(), _img(O_IMG_PA), _img(O_IMG_ARTIST), _img(O_IMG_OUTCOME), _img(A_IMG_EVENING),
          _img(A_IMG_SAME))
FOREST = re.compile(r"#1f3b2e|var\(--ink\)|31,\s*59,\s*46,\s*1\)", re.I)
TERRA = re.compile(r"#bd6a46|#a4532f", re.I)


def m12_redesign(page, shown):
    """M12 (extended 17 Oct 2026, EDITORIAL REDESIGN). The redesign keeps its
    promises: every photograph is the source's own tag, never two in a row;
    deep forest only behind the assessments; terracotta never a background;
    no two bands of one colour in a row; headline cautions on view and moved
    cautions inside a labelled expander; one labelled in-page navigation."""
    mi, me = shown.index('<main id="pn-main">'), shown.index("</main>")
    main = shown[mi:me]
    for tag in PHOTOS:
        if page.count(tag) != 1:
            die("M12 a photograph's source tag (file, alt text, dimensions) is not on the page exactly once: " + tag[:70])
    pics = [m.start() for m in re.finditer(r"<img\b", main)]
    if len(pics) != 5:
        die("M12 the main column must carry exactly the five source photographs (found %d)" % len(pics))
    for a, b in zip(pics, pics[1:]):
        if "<h2" not in main[a:b]:
            die("M12 two photographs sit side by side with no heading between them")
    css = page[page.index("<style>/* PLOTNUA-HOME-FOR-ART-MERGE"):]
    css = css[:css.index("</style>")]
    for sel, body in re.findall(r"([^{}]+)\{([^{}]*)\}", re.sub(r"/\*[\s\S]*?\*/", "", css)):
        for decl in re.findall(r"background(?:-color)?\s*:([^;]*)", body):
            if FOREST.search(decl) and not all(("is-forest" in x or "#discover-your-property" in x)
                                               for x in sel.split(",")):
                die("M12 deep forest is used as a background outside the assessment bands: " + sel.strip()[:70])
            if TERRA.search(decl):
                die("M12 terracotta is used as a background: " + sel.strip()[:70])
    forest = [m.start() for m in re.finditer(r'class="hfa-band is-forest', main)]
    if len(forest) != 1 or '<section class="hfa-band is-forest hfa-assess" id="hfa-checks-top"' not in main:
        die("M12 deep forest bands must be the assessment bands only")
    bands = [(m.start(), m.group(1)) for m in re.finditer(r'class="hfa-band is-(\w+)', main)]
    for (a, ca), (b, cb) in zip(bands, bands[1:]):
        if ca == cb and "<img" not in main[a:b]:
            die("M12 two %s bands sit in a row" % ca)
    def folded(pos):
        before = page[:pos]
        return before.count("<details") > before.count("</details>")
    for c in VISIBLE_CAUTIONS:
        hits = [m.start() for m in re.finditer(re.escape(c), page)]
        if not hits or all(folded(h) for h in hits):
            die("M12 a headline caution is not on view: " + c[:60])
    for c in FOLDED_CAUTIONS:
        i = page.find(c)
        if i < 0:
            die("M12 a caution was deleted rather than folded: " + c[:60])
        if folded(i):
            d = page.rindex("<details", 0, i)
            label = norm(page[d:page.index("</summary>", d)])
            if not label:
                die("M12 a folded caution sits in an unlabelled expander: " + c[:60])
    if shown.count('<nav class="hfa-nav" id="hfaNav" aria-label="%s">' % NAV_LABEL) != 1 or \
            re.findall(r'<li><a href="#([\w-]+)">', main[main.index('class="hfa-nav"'):]) [:5] != [a for a, _, _ in NAV_ITEMS]:
        die("M12 the in-page navigation is missing, unlabelled or out of order")
    for a, _, _ in NAV_ITEMS:
        if shown.count('id="%s"' % a) != 1:
            die("M12 the in-page navigation points at a missing anchor: #" + a)


def main(argv):
    if "--apply" not in argv and "--check" not in argv:
        print(__doc__); sys.exit(1)
    page = merged_page()
    if "--apply" in argv:
        (ROOT / MERGED).write_text(page, encoding="utf-8")
        (ROOT / OLD).write_text(REDIRECT, encoding="utf-8")
        apply_edits(True)
    else:
        if (ROOT / MERGED).read_text(encoding="utf-8") != page:
            print("CHECK FAILED: %s is out of date; run --apply" % MERGED); sys.exit(1)
        apply_edits(False)
    guards((ROOT / MERGED).read_text(encoding="utf-8"))
    print("A Home for Art: merged page, redirect and %d consolidation edits · %s — M1-M12 pass"
          % (len(CONSOLIDATION), "APPLIED" if "--apply" in argv else "CHECK OK"))


if __name__ == "__main__":
    main(sys.argv[1:])
