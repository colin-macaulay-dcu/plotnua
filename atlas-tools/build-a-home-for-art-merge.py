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
  M3  both Property Checks are linked from their branches and from the closing
      panel, always with ?start=1 (two-option entry, 14 Oct 2026); the merged
      page links nowhere to the old URL
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
      founder-approved question wording (CHECK24_APPROVED) is present.
      Revised 14 Oct 2026 (founder UX direction): the check's PRESENTATION
      (layout, styles, result copy, the floating Back control) was redesigned,
      so a whole-page byte comparison no longer applies; what decides a
      result is still pinned to BASE.
  M9  every consolidation edit applied exactly once
  M10 the founder's hierarchy: hosting story first, Open > Live with > Discover & own
  M11 ORIGINAL HOSTING IMAGERY (founder image correction, 13 Oct 2026): the hero
      is DISC-024's own published hero (dfb125ba9dd7cd87, DISC-024-03-Gallery-
      at-Home) with its own alt text; the hosting sequence follows it in its
      original order (046ec -> 6442d -> 05cab54); the buyer hero c0f5bf is not
      on the page; every card that represents this Discovery shows the hosting
      image

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
LEDE = ("An original artwork could become part of your everyday life. You might discover a piece to own, "
        "experience an artist&rsquo;s work in your home before deciding whether to buy it, or offer space "
        "that helps an artist reach a new audience.")
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
# TAKE PART (founder decision, 14 Oct 2026, 20:33): two complementary pathways
# in the PlotArt section, after "This matching service is not live yet.".
# Rendered ONLY while build-artist-register.py has ARTIST_PUBLIC = True (its
# guard A11 checks the result). Founder wording, verbatim; the two short
# audience labels are interface wording. The homeowner pathway is the existing
# check (?start=1), whose result offers the existing Art Space Register.
TAKE_H = "Take part"
TAKE_HOME = ("For homeowners", "I have a space for art",
             "Five short questions about your space. At the end, you can choose to join the Art Space Register.")
TAKE_ARTIST = ("For artists", "I&rsquo;m an artist looking for space",
               "Tell PlotArt what you make and the kind of space your work needs.")
TAKE_NOTE = ("Both are expressions of interest only: free, private and non-binding. Nothing is matched or "
             "arranged, and PlotNua has not verified any space or artist.")
ARTIST_PAGE = "artist-register.html"
# BE PART OF THE IDEA (founder request, 14 Oct 2026, 21:11): a compact top-of-page
# invitation to the same two pathways, closing the "Three possibilities" intro so
# it does not interrupt the opening story. Founder wording, verbatim. The lower
# Take part section is unchanged. Rendered only while the Artist Register is open.
INVITE_H = "Be part of the idea"
INVITE_P = ("Have a space that could host art? Or are you an artist looking for somewhere to show your work? "
            "PlotArt is inviting expressions of interest from both homeowners and artists.")
INVITE_B1 = "I have a space for art"
INVITE_B2 = "I&rsquo;m an artist looking for space"
# Interface wording (labels, signposts) — new, non-factual, declared.
NEW_TEXT = ["A Home for Art", OVERLOOKED_H2, "The overlooked opportunity", HERO_SUB, HERO_INTRO, LEDE, B1[0], B1[1], B2[0], B2[1], B3[0], B3[1], B2_P1, B2_P2,
            CHECK23, CHECK24, "Possibility one", "Possibility two", "Possibility three",
            "Three possibilities. One home.", "Which sounds like you?",
            "Before anything arrives, the custody, insurance and money questions below apply here too.",
            "If you come to love the work:", "The questions below are the same ones a host would ask.",
            "Buying or commissioning", "Living with or hosting work",
            "Two short checks. Nothing about your address.",
            "Check this against your own home", "Finding each other",
            "Explore What Could You Build in Your Garden? &rarr;", "See all Discoveries &rarr;",
            "Back to the homepage", "Continue Exploring", "Related Discoveries", "Underused Ground",
            "The Borrowed Garden", "Room To Build", "What Could You Build in Your Garden?", "On Screen",
            "Your Home on Screen", "Explore another possibility",
            TAKE_H, TAKE_HOME[0], TAKE_HOME[1], TAKE_HOME[2], TAKE_ARTIST[0], TAKE_ARTIST[1], TAKE_ARTIST[2], TAKE_NOTE,
            INVITE_H, INVITE_P, INVITE_B1, INVITE_B2]

TITLE = "A Home for Art: Host, Live With or Buy Original Irish Art | PlotNua"
DESC = ("Open your home to art by offering space for an artist&rsquo;s finished work, live with an artist&rsquo;s work "
        "by direct arrangement, or find, buy or commission original Irish art. What to agree, insure and settle in Ireland.")
OG_T = "A Home for Art | PlotNua Discoveries"
OG_D = "Your home could be more than somewhere to hang art. Three possibilities, one home, and you decide how far to go."

MERGE_CSS = """<style>/* PLOTNUA-HOME-FOR-ART-MERGE · generated by atlas-tools/build-a-home-for-art-merge.py.
   Branch chooser, branch openings, branch check calls and the two-check panel.
   Existing tokens only. */
  .hfa-lede{ font-family:'Fraunces',Georgia,serif; font-size:clamp(20px,2.3vw,25px); line-height:1.55;
    color:var(--ink); max-width:40ch; margin:0; }
  .hfa-choose{ margin:44px 0 0; }
  .hfa-choose-h{ font-family:'Work Sans',sans-serif; font-size:12px; letter-spacing:.16em; text-transform:uppercase;
    color:var(--accent); margin:0 0 16px; font-weight:500; }
  .hfa-paths{ list-style:none; margin:0; padding:0; display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:14px; }
  .hfa-path{ display:block; height:100%; box-sizing:border-box; padding:22px 22px 24px; background:var(--paper);
    border:1px solid rgba(31,59,46,.12); border-top:2px solid rgba(31,59,46,.45); border-radius:2px;
    text-decoration:none; color:var(--ink); transition:border-color .3s ease; }
  .hfa-path:hover{ border-top-color:var(--accent); }
  .hfa-path:focus-visible{ outline:2px solid var(--accent); outline-offset:3px; }
  .hfa-path-n{ display:block; font-family:'Work Sans',sans-serif; font-size:10.5px; letter-spacing:.2em;
    text-transform:uppercase; color:var(--accent); margin-bottom:12px; }
  .hfa-path-t{ display:block; font-family:'Fraunces',Georgia,serif; font-size:21px; line-height:1.25; margin-bottom:8px; }
  .hfa-path-l{ display:block; font-size:14.5px; line-height:1.6; color:var(--soft); }
  .hfa-branch{ scroll-margin-top:84px; border-top:2px solid rgba(31,59,46,.55); }
  .hfa-branch-lead{ font-size:18px; line-height:1.6; color:var(--soft); max-width:46ch; }
  #before-anything-arrives{ scroll-margin-top:84px; }
  .hfa-jump{ color:var(--accent); text-decoration:none; border-bottom:1px solid rgba(79,107,74,.35); }
  .hfa-jump:hover{ border-bottom-color:var(--accent); }
  .hfa-jump:focus-visible{ outline:2px solid var(--accent); outline-offset:3px; }
  .hfa-cta{ margin:34px 0 0; padding:26px 0 0; border-top:1px solid rgba(31,59,46,.12); }
  .hfa-cta .btn-primary{ margin-top:0; text-decoration:none; }
  .hfa-cta .btn-primary:focus-visible,.hfa-check .btn-primary:focus-visible{ outline:2px solid var(--accent); outline-offset:3px; }
  .hfa-cta-note{ margin:14px 0 0; font-size:14.5px; line-height:1.65; color:var(--soft); max-width:56ch; }
  .hfa-checks{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:22px; width:100%; max-width:860px;
    margin:8px auto 0; text-align:left; }
  .hfa-check{ background:var(--paper); padding:26px 26px 28px; border:1px solid rgba(31,59,46,.12); border-radius:2px; }
  .hfa-check h3{ font-family:'Fraunces',Georgia,serif; font-weight:400; font-size:21px; line-height:1.3; margin:0 0 8px; color:var(--ink); }
  .hfa-check p{ font-size:14.5px; line-height:1.6; color:var(--soft); margin:0; }
  .hfa-check .btn-primary{ text-decoration:none; }
  .hfa-take{ margin:30px 0 0; padding:26px 0 0; border-top:1px solid rgba(31,59,46,.12); }
  .hfa-take .hfa-paths{ grid-template-columns:repeat(2,minmax(0,1fr)); }
  .hfa-take .hfa-path-t::after{ content:"\\2192" / ""; margin-left:.35em; color:var(--accent); }
  .hfa-take .dq-note{ margin-top:16px; }
  @media(max-width:820px){ .hfa-take .hfa-paths{ grid-template-columns:1fr; } }
  .hfa-invite{ margin:40px 0 0; }
  .hfa-invite-actions{ display:flex; flex-wrap:wrap; gap:12px; margin-top:20px; }
  .hfa-invite .btn-primary{ margin-top:0; text-decoration:none; }
  .hfa-invite .btn-primary:focus-visible{ outline:2px solid var(--accent); outline-offset:3px; }
  @media(max-width:560px){ .hfa-invite-actions .btn-primary{ flex:1 1 100%; text-align:center; box-sizing:border-box; } }
  @media(max-width:820px){ .hfa-paths,.hfa-checks{ grid-template-columns:1fr; } }
</style>
"""


def artist_public():
    import importlib.util
    spec = importlib.util.spec_from_file_location("artist_register", ROOT / "atlas-tools" / "build-artist-register.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod.ARTIST_PUBLIC is True


def invite():
    return ('    <!-- PLOTNUA-BE-PART · top-of-page invitation to the two expressions of interest (founder,\n'
            '         14 Oct 2026). Shown only while the Artist Register is open. No form here. -->\n'
            '    <aside class="hfa-check hfa-invite" aria-labelledby="hfaInviteH">\n'
            '      <h3 id="hfaInviteH">%s</h3>\n'
            '      <p>%s</p>\n'
            '      <div class="hfa-invite-actions"><a class="btn-primary" href="%s">%s</a>'
            '<a class="btn-primary" href="%s">%s</a></div>\n'
            '    </aside>\n' % (INVITE_H, INVITE_P, START24, INVITE_B1, ARTIST_PAGE, INVITE_B2))


def take_part():
    card = ('      <li><a class="hfa-path" href="%s"><span class="hfa-path-n">%s</span>'
            '<span class="hfa-path-t">%s</span><span class="hfa-path-l">%s</span></a></li>\n')
    return ('    <!-- PLOTNUA-TAKE-PART · two expressions of interest (founder decision, 14 Oct 2026). Shown only\n'
            '         while the Artist Register is open. No form here; nothing is matched or arranged. -->\n'
            '    <nav class="hfa-choose hfa-take" aria-labelledby="hfaTakeH">\n'
            '      <p class="hfa-choose-h" id="hfaTakeH">%s</p>\n'
            '    <ul class="hfa-paths">\n%s%s    </ul>\n'
            '    <p class="dq-note">%s</p>\n'
            '    </nav>\n' % (TAKE_H, card % ((START24,) + TAKE_HOME), card % ((ARTIST_PAGE,) + TAKE_ARTIST), TAKE_NOTE))


def branch_open(n, bid, name, line):
    return ('  <section class="article-section reveal hfa-branch" id="%s">\n'
            '    <div class="kicker">%s</div>\n'
            '    <h2>%s</h2>\n'
            '    <p class="hfa-branch-lead">%s</p>\n' % (bid, n, name, line))


def cta(href, label, note):
    return ('    <div class="hfa-cta"><a class="btn-primary" href="%s">%s</a>\n'
            '      <p class="hfa-cta-note">%s</p></div>\n' % (href, label, note))


def main_html():
    # VISUAL AND NARRATIVE PRIORITY CORRECTION (founder, 13 Oct 2026): the hosting
    # story leads. Order: the overlooked opportunity (SPACE <-> SPACE) -> before
    # and after in pictures -> three possibilities -> Open your home (primary) ->
    # Live with art -> Discover & own -> shared guidance -> both checks.
    paths = "".join(
        '      <li><a class="hfa-path" href="#%s"><span class="hfa-path-n">%s</span>'
        '<span class="hfa-path-t">%s</span><span class="hfa-path-l">%s</span></a></li>\n' % (a, n, t, l)
        for a, n, (t, l) in (("open-your-home-to-art", "Possibility one", B3), ("live-with-art", "Possibility two", B2),
                             ("discover-and-own", "Possibility three", B1)))
    intro = ('  <section class="article-section reveal">\n'
             '    <div class="kicker">Three possibilities. One home.</div>\n'
             '    <p class="hfa-lede">%s</p>\n'
             '    <nav class="hfa-choose" aria-labelledby="hfaChooseH">\n'
             '      <p class="hfa-choose-h" id="hfaChooseH">Which sounds like you?</p>\n'
             '    <ul class="hfa-paths">\n%s    </ul>\n    </nav>\n'
             '%s'
             '  </section>\n' % (LEDE, paths, invite() if artist_public() else ""))
    split_at = O_FIRST.index('    <p class="dq-note"><strong>Nobody has to come to your door.</strong>')
    first_a = O_FIRST[:split_at].rsplit("\n\n", 1)[0] + "\n"     # opening line + SPACE <-> SPACE
    first_b = O_FIRST[split_at:].rsplit("  </section>\n", 1)[0]    # no visitors, the ladder, money
    overlooked = first_a.replace('  <section class="article-section reveal">\n',
                                 '  <section class="article-section reveal">\n'
                                 '    <div class="kicker">The overlooked opportunity</div>\n'
                                 '    <h2>%s</h2>\n' % OVERLOOKED_H2, 1) + "  </section>\n"
    # The hosting hero leads again, so the hosting plates keep their original
    # alt text and order: the same room empty -> the artist -> (after the
    # ladder) the outcome. (The earlier "after" plate repeated the hero.)
    before_plate = O_IMG_PA
    display_li = re.search(r'<li>\s*<span class="dq-adv-label">Display</span>\s*(<span class="dq-fact">.*?</span>)\s*'
                           r'(<span class="dq-note">.*?</span>)\s*</li>', O_FIRST, re.S)
    seller = "<strong>The artist is the seller.</strong> They own the work, set the price, deal with the buyer and receive the payment."
    if seller not in O0:
        die("M1 source sentence moved: the artist is the seller")
    b_open = (branch_open("Possibility one", "open-your-home-to-art", B3[0], B3[1]) +
              first_b + cta(START24, CHECK24, SUB24) + "  </section>\n")
    b_live = (branch_open("Possibility two", "live-with-art", B2[0], B2[1]) +
              '    <p>%s</p>\n    <p><strong>%s</strong></p>\n' % (B2_P1, B2_P2) +
              '    <div class="dq-adv">\n      <span class="dq-cat dq-adv-cat">Display</span>\n'
              '      <ul class="dq-rows">\n        <li>%s\n            %s</li>\n      </ul>\n    </div>\n'
              % (display_li.group(1), display_li.group(2)) +
              '    <p class="dq-note"><strong>If you come to love the work:</strong> %s</p>\n' % seller.replace(
                  "<strong>The artist is the seller.</strong>", "the artist is the seller.") +
              '    <p class="dq-note"><a class="hfa-jump" href="#before-anything-arrives">Before anything arrives, the custody, insurance '
              'and money questions below apply here too.</a></p>\n' +
              cta(START24, CHECK24, SUB24) + "  </section>\n")
    b_own = branch_open("Possibility three", "discover-and-own", B1[0], B1[1]) + "  </section>\n"
    settle = O_SETTLE.replace('<section class="article-section reveal">',
                              '<section class="article-section reveal" id="before-anything-arrives">', 1)
    before_cta = A_BEFORE.rsplit("  </section>\n", 1)[0] + cta(START23, CHECK23, SUB23) + "  </section>\n"
    future = (A_FUTURE.rsplit("  </section>\n", 1)[0] +
              '    <h3>Finding each other</h3>\n' +
              "".join(re.findall(r"    <p[^>]*>.*?</p>\n", O_FUTURE, re.S)))
    anchor = '    <p class="dq-note">This matching service is not live yet.</p>\n'
    if not future.endswith(anchor):
        die("M6 the PlotArt section no longer ends with the not-live sentence")
    future += (take_part() if artist_public() else "") + "  </section>\n"
    art = lambda *xs: '<div class="article">\n\n' + "\n".join(xs) + '\n</div>\n\n'
    return ('<main id="pn-main">\n' +
            art(overlooked) +
            before_plate + "\n" + O_IMG_ARTIST + "\n" +
            art(intro) +
            art(b_open) + O_IMG_OUTCOME + "\n" +
            art(b_live) + A_IMG_EVENING + "\n" +
            art(b_own, A_WHY, A_BUYING, A_SIZE) + A_IMG_SAME + "\n" +
            art(A_LOOK, A_COMM, before_cta) +
            art(settle) +
            art(O_BETTER) +
            art(A_FAQ, future).rstrip("\n") + "\n</main>\n")


PANEL = ('<section class="pb-preview reveal" id="discover-your-property">\n'
         '    <!-- TWO INDEPENDENT PROPERTY CHECKS (A Home for Art merge, 13 Oct 2026). Engines, questions,\n'
         '         outcomes and My Plot save keys unchanged. No form and no field here. -->\n'
         '    <div class="pn-wordmark">PlotNua</div>\n'
         '    <h2 class="pb-headline">Check this against your own home</h2>\n'
         '    <p class="pb-subhead">Two short checks. Nothing about your address.</p>\n'
         '    <div class="hfa-checks">\n'
         '      <div class="hfa-check"><h3>Living with or hosting work</h3><p>%s</p>\n'
         '        <a class="btn-primary" href="%s">%s</a></div>\n'
         '      <div class="hfa-check"><h3>Buying or commissioning</h3><p>%s</p>\n'
         '        <a class="btn-primary" href="%s">%s</a></div>\n'
         '    </div>\n'
         '    <div class="cs-exits">\n'
         '      <a class="cs-exit" href="discovery-living-in-the-garden.html">Explore What Could You Build in Your Garden? &rarr;</a>\n'
         '      <a class="cs-exit" href="discoveries.html">See all Discoveries &rarr;</a>\n'
         '      <a class="cs-exit is-home" href="index.html">Back to the homepage</a>\n'
         '    </div>\n'
         '  </section>\n' % (SUB24, START24, CHECK24, SUB23, START23, CHECK23))


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
    return s[:i] + rel + s[j:]


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
            die("M9 consolidation edit not found exactly once in %s: %s" % (f, old.strip()[:70]))
        if write:
            p.write_text(t.replace(old, new), encoding="utf-8")
        else:
            die("M9 consolidation edit not applied in %s: %s" % (f, old.strip()[:70]))


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
    if page.count('href="%s"' % START23) < 2 or page.count('href="%s"' % START24) < 3:
        die("M3 the Property Checks are not linked from their branches and the panel")
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
    order = [page.find(x) for x in (HOST_HERO_TAG, "<h2>%s</h2>" % OVERLOOKED_H2, "assets/img/046ec577a454599b.jpg",
                                     "assets/img/6442d19ec2dd1df0.jpg", 'class="hfa-paths"',
                                     'id="open-your-home-to-art"', "assets/img/05cab54ac0af83d0.jpg", 'id="live-with-art"', 'id="discover-and-own"',
                                     'id="before-anything-arrives"', "<h3>Living with or hosting work</h3>",
                                     "<h3>Buying or commissioning</h3>")]
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
    if art_entry().entry_revert(C23, (ROOT / C23).read_text(encoding="utf-8")) != head23:
        die("M8 the DISC-023 check changed beyond the two-option entry")


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
    print("A Home for Art: merged page, redirect and %d consolidation edits · %s — M1-M11 pass"
          % (len(CONSOLIDATION), "APPLIED" if "--apply" in argv else "CHECK OK"))


if __name__ == "__main__":
    main(sys.argv[1:])
