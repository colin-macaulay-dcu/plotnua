#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GARDEN RETREAT · COMPLETE EXPERIENCE RESTRUCTURE · BOUNDED BUILDER (v1)

Founder-approved implementation brief, 14 October 2026 ("Garden Retreat —
complete experience restructure & maker integration"). The page becomes:

  A  hero: headline, one line, two actions (compare / explore makers).
     NO "Check your garden" action: no Garden Retreat check exists, and the
     brief says "Do not invent a check".
  B  three option cards (sauna, hot tub, cold plunge): the page's own
     images, labelled, one example price, one key consideration, the
     original branch prose kept whole behind "More about ...", a route to
     the maker directory.
  C  one compact comparison table (space, price, power/heat, water, base
     and installation, planning, upkeep) -- every cell restates a figure or
     sentence already on the page, nothing new is claimed.
  D  "Could it work for your property?": what a check would establish, that
     it is not built, and what it cannot establish. No route is invented.
  E  the maker directory (atlas-tools/build-maker-explorer.py owns it).
  F  practical considerations: the planning short answer and the electrical
     warning stay VISIBLE; everything else is an accordion.
  G  evidence: every source an accordion.

COPY IS MOVED, NOT REWRITTEN. Every claim the Cluster 2 guards protect
(atlas-tools/prove-cluster2-garden-retreat.mjs, L1-L6, R1-R3, P1, E1, S1,
S2, J1-J3) is lifted VERBATIM from the page by exact anchors: if an anchor
is not found exactly once the build refuses. Removed: the three intro
sections (folded into the hero and section B), the OGNYX image section
(the brief: OGNYX is not a standalone catalogue in the editorial), the
"How far" section (folded into D), "Where this is sold" (condensed into a
note under C, keeping the supplier set and the no-relationship note).

  python3 atlas-tools/build-garden-retreat-restructure.py --apply   (BEFORE -> AFTER)
  python3 atlas-tools/build-garden-retreat-restructure.py --check   (guards on AFTER)

GUARDS (run by --check, and on the output of --apply before it is written)
  GR1 sections in the brief's order, each exactly once
  GR2 the hero offers exactly two actions, both to sections on this page
  GR3 no OGNYX (or any supplier) image on the page; no maker image section
      (30 Oct 2026: except inside the Premium Supplier Gallery region, which is
      rights-guarded per asset by atlas-tools/prove-supplier-gallery.py)
  GR4 the planning short answer and the electrical warning are VISIBLE
      (outside every <details>)
  GR5 every <details> has a <summary> (keyboard-operable natively)
  GR6 the default view is materially shorter: visible words outside closed
      accordions <= 55% of the 2,994 measured before
  GR7 no internal governance or permission language reaches the reader
  GR8 no "Irish availability is confirmed for 0" style statement
  GR10 no maker held from the directory (MyCabin, Cosy Cabins, Sommarnöjen,
       Auroom) is named anywhere on the page (14 Oct 2026)
  GR9 nothing outside <main>, the hero copy, the CSS block, dateModified and
      the sitemap lastmod changes
"""
import html
import pathlib
import re
import sys

# PREMIUM LOCK (founder decision, 23 Oct 2026): refuse before reading or writing anything
# when a page this layout builder rewrites carries the approved Premium design.
if __name__ == "__main__":
    import os as _pl_os, sys as _pl_sys
    _pl_sys.path.insert(0, _pl_os.path.dirname(_pl_os.path.abspath(__file__)))
    import premium_pages as _pl
    _pl.refuse_if_premium("build-garden-retreat-restructure.py", ['discovery-garden-retreat.html'])

ROOT = pathlib.Path(__file__).resolve().parent.parent
PAGE = ROOT / "discovery-garden-retreat.html"
SITEMAP = ROOT / "sitemap.xml"
MARK = "PLOTNUA-GR-RESTRUCTURE-V1"
TODAY = "2026-10-14"
WORDS_BEFORE = 2994          # measured 14 Oct 2026 at 1280/768/375/320 (identical)
EXPLORER_START = "  <!-- 6c · PLOTNUA-MAKER-EXPLORER-V1"
CSS_BEGIN = "/* PLOTNUA-GR-MAKER-IMAGERY-CSS-BEGIN"
CSS_END = "/* PLOTNUA-GR-MAKER-IMAGERY-CSS-END */\n"
NEW_CSS_BEGIN = "/* PLOTNUA-GR-RESTRUCTURE-CSS-BEGIN"
NEW_CSS_END = "/* PLOTNUA-GR-RESTRUCTURE-CSS-END */\n"


def die(m):
    print("REFUSED: " + m)
    sys.exit(2)


def one(src, s, what):
    if src.count(s) != 1:
        die("%s: anchor found %d times: %r" % (what, src.count(s), s[:70]))
    return src.index(s)


def cut(src, a, b, what, keep_b=False):
    """The text from anchor a (inclusive) to anchor b (exclusive)."""
    i = one(src, a, what + " start")
    j = src.find(b, i + len(a))
    if j < 0:
        die(what + ": end anchor not found")
    return src[i:j + (len(b) if keep_b else 0)]


def inner_paras(section_html):
    """The <p> elements of a branch section, verbatim."""
    ps = re.findall(r"    <p>.*?</p>\n", section_html, re.S)
    if not ps:
        die("branch prose not found")
    return "".join("      " + p.lstrip() for p in ps)


CSS = NEW_CSS_BEGIN + """ · Garden Retreat restructure (14 Oct 2026).
   Built by atlas-tools/build-garden-retreat-restructure.py; page tokens only.
   Images are shown whole at their natural ratio (no crop). */
  .gr-hero-actions{ margin:26px auto 0; display:flex; flex-wrap:wrap; gap:12px; justify-content:center; }
  .gr-hero-actions a{ display:inline-block; padding:14px 22px; border-radius:2px; text-decoration:none;
    font:500 13px/1.2 'Work Sans',sans-serif; letter-spacing:.08em; text-transform:uppercase; }
  .gr-hero-actions .is-primary{ background:var(--brand-ivory); color:var(--ink); }
  .gr-hero-actions .is-secondary{ color:var(--brand-ivory); border:1px solid rgba(248,245,236,.75);
    background:rgba(15,14,10,.18); }
  .gr-hero-actions a:hover{ opacity:.92; }
  .gr-hero-actions a:focus-visible{ outline:2px solid var(--brand-ivory); outline-offset:3px; }
  .gr-cards{ list-style:none; margin:34px 0 0; padding:0; display:grid; grid-template-columns:1fr; gap:22px; align-items:start; }
  @media (min-width:900px){ .gr-cards{ grid-template-columns:repeat(3,1fr); gap:20px; } }
  @media (min-width:600px) and (max-width:899px){ .gr-cards{ grid-template-columns:1fr 1fr; } }
  .gr-card{ background:var(--paper); border:1px solid rgba(31,59,46,.10); border-radius:3px;
    display:flex; flex-direction:column; min-width:0; }
  .gr-card-img{ margin:0; position:relative; }
  .gr-card-img img{ display:block; width:100%; height:auto; border-radius:3px 3px 0 0; background:var(--cream); }
  .gr-card-label{ position:absolute; left:10px; bottom:10px; font:500 10px/1 'Work Sans',sans-serif;
    letter-spacing:.14em; text-transform:uppercase; color:var(--ink); background:rgba(248,245,236,.88);
    padding:5px 7px; border-radius:2px; }
  .gr-card-body{ padding:18px 20px 20px; display:flex; flex-direction:column; flex:1; }
  .gr-card h3{ font-size:clamp(20px,2vw,23px); margin:0 0 8px; }
  .article-section .gr-card p{ font-size:15px; line-height:1.65; max-width:none; }
  .article-section .gr-card p + p{ margin-top:12px; }
  .gr-card-fact{ display:block; font:500 10px/1.2 'Work Sans',sans-serif; letter-spacing:.16em;
    text-transform:uppercase; color:var(--accent); margin-bottom:3px; }
  .gr-card-more{ margin-top:14px; border-top:1px solid rgba(31,59,46,.10); }
  .gr-card-more summary{ cursor:pointer; padding:12px 0 4px; font:500 14px 'Work Sans',sans-serif; color:var(--accent); }
  .gr-card-more summary:focus-visible{ outline:2px solid var(--accent); outline-offset:3px; }
  .article-section .gr-card-more p{ font-size:14.5px; }
  .gr-card-link{ margin-top:auto; padding-top:16px; font:500 14px 'Work Sans',sans-serif; color:var(--accent);
    text-decoration:none; }
  .gr-card-link span{ border-bottom:1px solid rgba(79,107,74,.35); }
  .gr-cmp-wrap{ margin-top:30px; }
  .gr-cmp{ width:100%; border-collapse:collapse; font-size:14.5px; line-height:1.55; color:var(--soft); }
  .gr-cmp caption{ text-align:left; font-size:14px; color:var(--soft); padding-bottom:12px; }
  .gr-cmp th, .gr-cmp td{ text-align:left; vertical-align:top; padding:12px 14px 12px 0;
    border-top:1px solid rgba(31,59,46,.10); }
  .gr-cmp thead th{ font-family:'Fraunces',serif; font-weight:500; font-size:17px; color:var(--ink); border-top:none; }
  .gr-cmp tbody th{ font:500 10px/1.5 'Work Sans',sans-serif; letter-spacing:.16em; text-transform:uppercase;
    color:var(--soft); width:16%; padding-top:15px; }
  .gr-cmp td strong{ color:var(--ink); font-weight:600; }
  .gr-cmp .gr-cmp-ex{ display:block; font-size:12.5px; }
  @media (max-width:760px){
    .gr-cmp thead{ position:absolute; width:1px; height:1px; overflow:hidden; clip:rect(0 0 0 0); }
    .gr-cmp, .gr-cmp tbody, .gr-cmp tr, .gr-cmp th, .gr-cmp td{ display:block; width:auto; }
    .gr-cmp tr{ padding:14px 0 6px; border-top:1px solid rgba(31,59,46,.14); }
    .gr-cmp th, .gr-cmp td{ border-top:none; padding:3px 0; }
    .gr-cmp tbody th{ padding:0 0 6px; width:auto; }
    .gr-cmp td::before{ content:attr(data-label); display:block; font-weight:600; color:var(--ink); font-size:13.5px; }
    .gr-cmp td{ padding-bottom:10px; }
  }
  .gr-cmp-lines{ margin-top:22px; }
  .gr-note{ margin-top:22px; font-size:14.5px !important; line-height:1.7 !important; }
  .gr-list{ margin:18px 0 0; padding-left:1.1em; color:var(--soft); font-size:16px; line-height:1.75; max-width:60ch; }
  .gr-list li + li{ margin-top:6px; }
  .article-section .gr-list + p{ margin-top:20px; }
  #compare .rel-note{ margin-top:14px; font-size:14.5px; line-height:1.7; }
  .gr-acc{ margin-top:6px; }
  .gr-acc summary h3{ font-size:clamp(18px,1.9vw,21px); }
  .gr-acc summary:focus-visible{ outline:2px solid var(--accent); outline-offset:3px; }
  .gr-acc .faq-a > p{ font-size:16px; }
  .gr-acc .faq-a .rule-group:first-child{ margin-top:0; }
  .gr-warn{ margin-top:28px; padding:18px 20px; background:var(--paper); border-left:2px solid rgba(31,59,46,.42); }
  .practical-group .gr-warn:first-child{ padding-top:18px; }
  #explore-makers .mx-plist li .mx-pp{ grid-column:1; font-size:13px; color:var(--ink); }
  /* Product navigation (14 Oct 2026, pre-launch corrections): the maker's own
     page, authorised images shown whole with label and credit, and the
     product a link pointed to. */
  #explore-makers .mx-plist li .mx-ext{ grid-column:1; justify-self:start; margin-top:4px; font-size:13px;
    font-weight:500; color:var(--accent); text-decoration:none; border-bottom:1px solid rgba(79,107,74,.35); }
  #explore-makers .mx-plist li .mx-ext:hover{ border-bottom-color:var(--accent); }
  #explore-makers .mx-plist li .mx-ext:focus-visible{ outline:2px solid var(--accent); outline-offset:3px; }
  #explore-makers .mx-plist li .mx-imgs{ grid-column:1; display:flex; flex-wrap:wrap; gap:10px; margin:8px 0 2px; }
  #explore-makers .mx-img{ margin:0; width:132px; }
  #explore-makers .mx-img img{ display:block; width:100%; height:auto; border-radius:2px; background:var(--cream); }
  #explore-makers .mx-img figcaption{ margin-top:4px; font-size:11px; line-height:1.4; color:var(--soft); }
  #explore-makers .mx-img-kind{ display:block; font-size:9.5px; letter-spacing:.14em; text-transform:uppercase; color:var(--accent); }
  #explore-makers .mx-img figcaption a{ color:var(--ink); text-decoration:underline; text-underline-offset:2px; }
  #explore-makers .mx-plist li.mx-target{ background:rgba(79,107,74,.09); box-shadow:inset 3px 0 0 var(--accent);
    padding-left:10px; }
  #explore-makers p.mx-credit{ margin-top:6px; }
  /* Mobile (14 Oct 2026): the first screen ends with a 140px caption band.
     The hero stops 140px short of the fold; the caption sits at the top of
     that band and the floating Back control (fixed, 16px from the bottom,
     44px tall) sits in its empty lower half -- so at load the Back covers
     neither the caption nor the first heading. Section rhythm is tightened. */
  @media (max-width:600px){
    .d-hero{ height:calc(100vh - 140px); height:calc(100svh - 140px); min-height:420px; }
    .gr-hero-cap{ box-sizing:border-box; min-height:140px; margin:0 auto; padding:14px 6vw 0; }
    #pn-main > .article > .article-section:first-child{ padding-top:24px; }
    .d-hero-copy{ padding-bottom:7vh; }
    .gr-hero-actions{ margin-top:18px; gap:10px; }
    .gr-hero-actions a{ padding:12px 18px; }
    #pn-main .article-section{ padding:46px 0; }
    #pn-main .article-section h2{ margin-bottom:18px; }
    .gr-cards{ margin-top:24px; gap:16px; }
    .gr-cmp tr{ padding:10px 0 2px; }
    .gr-cmp td{ padding-bottom:6px; }
  }
""" + NEW_CSS_END


def build(src):
    if MARK in src:
        die("the page is already restructured (state AFTER); nothing to apply")
    one(src, 'id="the-part-you-walk-past"', "BEFORE state")

    # ── fragments, verbatim ────────────────────────────────────────────────
    hero_copy = cut(src, '    <p class="subtitle">An ordinary garden', "\n  </div>\n</header>", "hero subtitle")
    img = {}
    for k, a in (("sauna", "  <!-- IMAGE B - THE COMPACT SAUNA."),
                 ("hot", "  <!-- IMAGE C - THE WOOD-FIRED HOT TUB."),
                 ("plunge", "  <!-- IMAGE D - THE COLD PLUNGE,")):
        block = cut(src, a, "  </section>\n", "image " + k, keep_b=True)
        comment = re.search(r"  <!--.*?-->\n", block, re.S).group(0)
        tag = re.search(r'<img [^>]+>', block).group(0)
        img[k] = (comment.replace("\n  ", "\n        ").replace("  <!--", "        <!--", 1), tag)
    prose = {k: inner_paras(cut(src, '<section class="article-section reveal" id="%s">' % sid,
                                "  </section>", k))
             for k, sid in (("sauna", "branch-sauna"), ("hot", "branch-hot-tub"),
                            ("plunge", "branch-cold-plunge"))}
    plan_short = cut(src, '    <div class="rule-group">\n      <h3>The short answer</h3>',
                     '    <div class="rule-group">\n      <h3>Why building', "planning short answer")
    plan_rest = cut(src, '    <div class="rule-group">\n      <h3>Why building',
                    '    <div class="practical-group">', "planning detail")
    items = {}
    for h in ("Electricity and fire", "Base and weight", "Water", "What it costs to run", "Insurance"):
        items[h] = cut(src, '      <div class="practical-item">\n        <h3>%s</h3>\n' % h,
                       "\n      </div>\n", h, keep_b=True)
    sold = cut(src, '    <p><a href="https://mycabin.ie/"', "  </section>", "where this is sold")
    sold_paras = re.findall(r"    <p.*?</p>\n", sold, re.S)
    if len(sold_paras) != 3:
        die("where-this-is-sold: expected three paragraphs")
    explorer = cut(src, EXPLORER_START, '  <section class="article-section reveal" id="where-this-comes-from">',
                   "maker explorer")
    ev = cut(src, '    <details class="faq-item is-inline">\n      <summary><h3>Supplier pages',
             "    <h3>What this evidence does not establish</h3>", "evidence drawers")
    not_est = cut(src, "    <h3>What this evidence does not establish</h3>\n    <p>",
                  "</p>\n  </section>", "evidence limits", keep_b=False)
    not_est_p = not_est.split("\n", 1)[1].strip()   # the <p>...  (closing </p> re-added)

    def body_of(item, h):
        """Inner markup of a practical item, without its own heading."""
        return item.split("<h3>%s</h3>\n" % h, 1)[1].rsplit("\n      </div>\n", 1)[0]

    def acc(h, inner, close="        </div>"):
        return ('      <details class="faq-item gr-acc">\n'
                '        <summary><h3>%s</h3><span class="icon"></span></summary>\n'
                '        <div class="faq-a">\n%s\n%s\n'
                '      </details>\n' % (h, inner, close))

    # ── A · hero ───────────────────────────────────────────────────────────
    # 14 Oct 2026 (controlled text-only expansion): "the makers selling them in
    # Ireland" became "the makers who publish them". The directory now lists
    # makers whose Irish delivery is not confirmed (TimberIN, a UK site), and no
    # wellness record states Irish availability, so the hero must not either.
    new_hero = ('    <p class="subtitle">A sauna, a hot tub or a cold plunge &mdash; one thing in one '
                'part of the garden. See what each asks of your garden, then the makers who publish '
                'them.</p>\n'
                '    <div class="gr-hero-actions">\n'
                '      <a class="is-primary" href="#compare">Compare the options</a>\n'
                # 31 Oct 2026 (founder, supplier-gallery consolidation release): the button opens
                # the unified supplier section; #explore-makers stays for existing deep links.
                '      <a class="is-secondary" href="#suppliers">Meet the makers</a>\n'
                '    </div>')

    # ── B · three cards ────────────────────────────────────────────────────
    CARDS = [
        ("sauna", "option-sauna", "Outdoor sauna",
         "A small timber cabin with a heater. It looks as though it needs the most room; "
         "it doesn&rsquo;t necessarily.",
         "&euro;8,700 including VAT &mdash; Hansa24 Lisette sauna cabin, about 7.6&nbsp;m&sup2;",
         "Ask which heater it comes with: electric needs a Registered Electrical Contractor, "
         "wood-fired needs a flue. The cabin needs a level, load-bearing base.",
         "More about saunas", "Browse saunas"),
        ("hot", "option-hot-tub", "Wood-fired hot tub",
         "Water heated by a wood-burning stove rather than an electric spa system.",
         "From &euro;4,340 &mdash; Gardenhouse24 Hot Tub DeLux 220, about 4&nbsp;m&sup2;",
         "Close to 1,900&nbsp;kg when full, plus a stove and flue to place safely.",
         "More about hot tubs", "Browse hot tubs"),
        ("plunge", "option-cold-plunge", "Cold plunge",
         "The smallest of the three: a cold-water tub at the edge of the garden.",
         "&euro;1,699 &mdash; Timbertrove cold-plunge tub, about 1.2&nbsp;m&sup2;",
         "Needs level ground and somewhere for the water to go. No chilling or filtration "
         "was evidenced for this model.",
         "More about cold plunges", "Browse cold plunges"),
    ]
    cards = []
    for k, cid, title, summ, price, key, more, browse in CARDS:
        comment, tag = img[k]
        cards.append(
            '      <li class="gr-card" id="%s">\n%s'
            '        <figure class="gr-card-img">%s<figcaption class="gr-card-label">Illustrative image</figcaption></figure>\n'
            '        <div class="gr-card-body">\n'
            '          <h3>%s</h3>\n'
            '          <p>%s</p>\n'
            '          <p><span class="gr-card-fact">Example price</span>%s</p>\n'
            '          <p><span class="gr-card-fact">Key consideration</span>%s</p>\n'
            '          <details class="gr-card-more">\n'
            '            <summary>%s</summary>\n%s'
            '          </details>\n'
            '          <a class="gr-card-link" href="#explore-makers"><span>%s from listed makers</span>&nbsp;&rarr;</a>\n'
            '        </div>\n'
            '      </li>\n' % (cid, comment, tag, title, summ, price, key, more,
                               prose[k].replace("      <p>", "            <p>"), browse))

    # ── C · comparison ─────────────────────────────────────────────────────
    ROWS = [
        ("Space", ["About 7.6&nbsp;m&sup2;: 3.65&nbsp;m by 2.08&nbsp;m outside; 7&nbsp;m&sup2; inside, two rooms",
                   "About 4&nbsp;m&sup2;: 2.26&nbsp;m across, plus a chimney",
                   "About 1.2&nbsp;m&sup2;: 1.25&nbsp;m across, a metre high"]),
        ("Product price", ["<strong>&euro;8,700</strong> including VAT. Heater not stated",
                           "<strong>&euro;4,340</strong>; &euro;6,430 as configured. Bubbles &euro;650",
                           "<strong>&euro;1,699</strong>. None published as extras"]),
        ("Power or heat", ["A heater, type not published: electric needs an electrician, wood a flue",
                           "Wood. Electricity only if you add bubbles, lights or a filter",
                           "None. No chilling or filtration evidenced"]),
        ("Water", ["None published", "1,650 litres. No supplier says where it should go",
                   "Fill it, use it, drain it. The route is yours to plan"]),
        ("Base and installation", ["Level and load-bearing. Installation not published: ask the maker",
                                   "Roughly 1,900&nbsp;kg full; a concrete base is sold. Installation a paid option",
                                   "Level ground. Flat-packed or assembled"]),
        ("Planning", ["A building: the garden-building rules apply",
                      "On an existing patio it appears to fall outside the rules; dig or build around it and it is back in",
                      "Stood on the ground, as for a hot tub on a patio"]),
        ("Upkeep", ["No routine published",
                    "The anti-rot warranty depends on the maker&rsquo;s care guidelines",
                    "No water-treatment routine published"]),
    ]
    heads = ["Compact sauna", "Wood-fired hot tub", "Cold plunge"]
    ex = ["Hansa24 Lisette sauna cabin", "Gardenhouse24 Hot Tub DeLux 220", "Timbertrove Cold Plunge &amp; Ice Bath"]
    thead = "".join('<th scope="col">%s<span class="gr-cmp-ex">%s</span></th>' % (h, e) for h, e in zip(heads, ex))
    tbody = ""
    for lab, cells in ROWS:
        tbody += ('          <tr><th scope="row">%s</th>%s</tr>\n'
                  % (lab, "".join('<td data-label="%s">%s</td>' % (h, c) for h, c in zip(heads, cells))))

    # ── assemble <main> ────────────────────────────────────────────────────
    main = (
        '<main id="pn-main">\n'
        '<!-- %s · built by atlas-tools/build-garden-retreat-restructure.py from the\n'
        '     page\'s own copy (founder brief, 14 Oct 2026). The maker directory below is\n'
        '     owned by atlas-tools/build-maker-explorer.py. Do not hand-edit. -->\n'
        '<div class="article">\n\n'
        '  <section class="article-section reveal" id="three-ways-in">\n'
        '    <div class="kicker">Start With One Thing</div>\n'
        '    <h2>Three ways in</h2>\n'
        '    <p>A garden retreat doesn&rsquo;t have to mean transforming the whole garden. It can begin '
        'with one thing in one part of it &mdash; and these three ask very different things of a garden. '
        'Each price below is one product PlotNua checked, not a finished-project cost.</p>\n'
        '    <ul class="gr-cards">\n%s    </ul>\n'
        '  </section>\n\n'
        '  <section class="article-section reveal" id="compare">\n'
        '    <div class="kicker">The Real Question</div>\n'
        '    <h2>What each one asks of your garden</h2>\n'
        '    <div class="gr-cmp-wrap">\n'
        '      <table class="gr-cmp">\n'
        '        <caption>Three products PlotNua checked directly. Not averages, not quotes.</caption>\n'
        '        <thead><tr><td></td>%s</tr></thead>\n'
        '        <tbody>\n%s        </tbody>\n'
        '      </table>\n'
        '    </div>\n'
        '    <p class="gr-cmp-lines"><strong>The cheapest way in is &euro;1,699 and about a square metre.</strong> '
        '<strong>Ask which heater the sauna comes with: it decides between an electrician and a flue.</strong> '
        '<strong>And the heaviest thing here is the water, not the structure.</strong></p>\n'
        '    <p class="hb-cmp-foot">Prices come from the suppliers&rsquo; own pages, read in September 2026, '
        'and they change. VAT is only shown where the supplier states it. None of these is a finished-project '
        'cost: bases, connections and site work are quoted separately. Planning is a reading of the rules, '
        'not a decision &mdash; see <a href="#the-practical-part">What you need to sort out</a>.</p>\n'
        '%s'
        '  </section>\n\n'
        '  <section class="article-section reveal" id="could-it-work">\n'
        '    <div class="kicker">Your Property</div>\n'
        '    <h2>Could it work for your property?</h2>\n'
        '    <p>That depends on your garden more than on the product: the clear space you have and where '
        'it is, whether power and water reach it, the ground, and what is already built there. '
        '<strong>PlotNua does not yet have a property check for garden retreats, and nothing on this page '
        'assesses your property.</strong> Start with these:</p>\n'
        '    <ul class="gr-list">\n'
        '      <li>Measure the clear space, and count what is already built in the garden: a shed counts '
        'towards the garden-building limits.</li>\n'
        '      <li>Check how far power and water would have to travel. Running them underground means '
        'digging.</li>\n'
        '      <li>Ask the maker to confirm delivery to your address, installation and the base it needs, '
        'in writing.</li>\n'
        '    </ul>\n'
        '    <p>One thing in one corner is a complete answer, and for most gardens it is probably the right '
        'one. Some people keep going: a tub one year, a sauna the next. <strong>PlotNua cannot tell you which '
        'of those steps your garden would take.</strong></p>\n'
        '  </section>\n\n'
        '%s'
        '  <section class="article-section reveal" id="the-practical-part">\n'
        '    <div class="kicker">The Practical Part</div>\n'
        '    <h2>What you need to sort out</h2>\n'
        '    <h3>Planning</h3>\n'
        '%s'
        '%s'
        '    <div class="practical-group">\n'
        '      <div class="practical-item gr-warn">\n'
        '        <h3>Electricity and fire</h3>\n%s\n'
        '      </div>\n'
        '%s%s%s%s'
        '    </div>\n'
        '  </section>\n\n'
        '  <section class="article-section reveal" id="where-this-comes-from">\n'
        '    <div class="kicker">The Evidence</div>\n'
        '    <h2>Where this comes from</h2>\n'
        '    <p>Every figure above came from a named source, on a stated date.</p>\n\n'
        '%s'
        '    <details class="faq-item is-inline">\n'
        '      <summary><h3>Maker directory</h3><span class="icon"></span></summary>\n'
        '      <div class="faq-a">Products and prices in the maker directory are read from each maker&rsquo;s '
        'own published product pages. A price is shown only where the maker publishes one, with the VAT '
        'position the maker states; where it does not say, the directory says so. Delivery, installation and '
        'lead times are not stated for any listed product: confirm them with the maker.</div>\n'
        '    </details>\n\n'
        '    <details class="faq-item is-inline">\n'
        '      <summary><h3>What this evidence does not establish</h3><span class="icon"></span></summary>\n'
        '      <div class="faq-a">%s</div>\n'
        '    </details>\n'
        '  </section>\n\n'
        '</div>\n'
        '</main>\n'
    ) % (MARK, "".join(cards), thead, tbody,
         "    <p class=\"gr-note\">" + sold_paras[0].strip()[3:-4] + " " +
         sold_paras[1].strip()[3:-4] + "</p>\n" + sold_paras[2].replace("    <p", "    <p", 1),
         explorer,
         plan_short,
         # The planning accordion closes at the rule-groups' own indent so the
         # Cluster 2 L5 guard's region ('</div>\n    </div>') ends exactly at
         # the end of the case it guards, as tightly as before the restructure.
         acc("Planning in more detail", plan_rest.rstrip("\n"), close="    </div>"),
         body_of(items["Electricity and fire"], "Electricity and fire"),
         acc("Base and weight", body_of(items["Base and weight"], "Base and weight")),
         acc("Water", body_of(items["Water"], "Water")),
         acc("What it costs to run", body_of(items["What it costs to run"], "What it costs to run")),
         acc("Insurance", body_of(items["Insurance"], "Insurance")),
         ev, not_est_p[3:] if not_est_p.startswith("<p>") else not_est_p)

    # ── splice ─────────────────────────────────────────────────────────────
    out = src.replace(hero_copy, new_hero, 1)
    m0 = one(out, '<main id="pn-main">', "main start")
    m1 = one(out, "</main>\n", "main end") + len("</main>\n")
    out = out[:m0] + main + out[m1:]
    c0 = one(out, CSS_BEGIN, "imagery CSS")
    c1 = one(out, CSS_END, "imagery CSS end") + len(CSS_END)
    out = out[:c0] + CSS + out[c1:]
    out = re.sub(r'"dateModified":\s*"[0-9-]+"', '"dateModified": "%s"' % TODAY, out, count=1)
    # ── THE SAUNA EXAMPLE (14 Oct 2026, final publication consistency
    # corrections). MyCabin is held from the Garden Retreat directory and
    # replied "This is not something we are interested in" (17 Sep 2026), so
    # its Cube Sauna M, price and showrooms leave the comparison. The
    # replacement is a product the directory publishes: Hansa24's Lisette
    # (G0093), Atlas recu6KOXm4cJngQHW -- external 365 x 208 cm, room area
    # 7 m2, two rooms, EUR 8,700 including VAT, heater not published -- read
    # from summerhouse24.ie in September 2026 and VERIFIED live on 14 Oct.
    # Each passage below is the base page's own text and must match exactly
    # once; nothing is inferred beyond the Atlas record.
    for old, new in SAUNA_EXAMPLE:
        if out.count(old) != 1:
            die("sauna-example passage not found exactly once: " + old[:70])
        out = out.replace(old, new)
    return out


LISETTE = "https://summerhouse24.ie/outdoor-sauna-cabin-lisette-g0093/"
SAUNA_EXAMPLE = [
    ("ELECTRIC arrangement, which is the one the evidenced MyCabin Cube M\n"
     "             ships with. The wood-fired option named in the copy is an option,\n"
     "             and the copy does not claim this photograph shows it.",
     "ELECTRIC arrangement; the evidenced Hansa24 Lisette publishes no\n"
     "             heater, so the copy names neither arrangement and does not claim\n"
     "             this photograph shows one."),
    ("As a sense of scale, MyCabin&rsquo;s Cube Sauna M is 3 metres by 2.17 metres &mdash; a little over "
     "6.5&nbsp;m&sup2; &mdash; and is sold as a four-to-six-person sauna at a published &euro;9,620 including VAT.",
     "As a sense of scale, Hansa24&rsquo;s Lisette sauna cabin is 3.65 metres by 2.08 metres outside "
     "&mdash; about 7.6&nbsp;m&sup2; &mdash; with a 7&nbsp;m&sup2; room area over two rooms, at a published "
     "&euro;8,700 including VAT."),
    ("Other models are smaller and larger, and several Irish suppliers do not publish dimensions at all. "
     "Across the three suppliers PlotNua checked, published garden-sauna prices run from about &euro;4,649 "
     "to &euro;11,650.",
     "Other models are smaller and larger, and some makers do not publish dimensions at all. The maker "
     "directory below lists each maker&rsquo;s published products and prices."),
    ("Electric heating brings electrical work with it. MyCabin also publishes a &euro;596 wood-fired heater "
     "option including the chimney system for this range. Choosing that route changes what has to be "
     "accommodated, because it introduces a stove and flue.",
     "Hansa24 does not publish which heater comes with it. Electric heating brings electrical work with it; "
     "a wood-fired stove brings a flue. Either changes what has to be accommodated, so settle the heater "
     "before the base."),
    ('<a href="https://mycabin.ie/" target="_blank" rel="noopener noreferrer">MyCabin</a> has showrooms in '
     'Blessington, Cobh and Wexford, and publishes the sauna sizes and prices above.',
     '<a href="' + LISETTE + '" target="_blank" rel="noopener noreferrer">Summerhouse24 Ireland</a> '
     '(Hansa24 Group) publishes the sauna&rsquo;s size and price above.'),
    ("The suppliers named in this section were not contacted: everything quoted here was read from their "
     "own public pages in September 2026.",
     "Everything quoted here was read from the suppliers&rsquo; own public pages in September 2026."),
    ("MyCabin&rsquo;s Cube Sauna M page, Gardenhouse24",
     "Hansa24&rsquo;s Lisette sauna cabin page on summerhouse24.ie, Gardenhouse24"),
]
# Makers the directory holds may not be named anywhere on the page (GR10).
HELD_NAME_RE = re.compile(r"my\s*cabin|cosy\s*cabins|sommarn|auroom", re.I)


# ── guards ───────────────────────────────────────────────────────────────────
ORDER = ["three-ways-in", "compare", "could-it-work", "explore-makers",
         "the-practical-part", "where-this-comes-from"]
GOVERNANCE = re.compile(r"\b(publication gate|governance|image permission|with its permission|authoris|held products?|"
                        r"public visibility|eligib|founder|atlas|qualification|rights record|"
                        r"what these look like|maker&rsquo;s own images|maker's own images)\b", re.I)


def visible_default(page):
    """Words a reader sees with every accordion closed (summaries count)."""
    m = page[page.index('<header class="d-hero'):page.index("</main>")]
    m = re.sub(r"<script.*?</script>", " ", m, flags=re.S)
    m = re.sub(r"<!--.*?-->", " ", m, flags=re.S)
    m = re.sub(r"<noscript>.*?</noscript>", " ", m, flags=re.S)
    # the AI disclosure beneath the hero (31 Oct 2026) is a required notice, not reading content; it is also
    # present twice in the markup (one per viewport), so it is not counted
    m = re.sub(r'<p class="pn-(?:compare__note|hero-note)">.*?</p>', " ", m, flags=re.S)
    m = re.sub(r"(<details[^>]*>\s*<summary>.*?</summary>).*?</details>", r"\1", m, flags=re.S)
    t = html.unescape(re.sub(r"<[^>]+>", " ", m))
    return len(re.findall(r"[A-Za-z0-9€][\w'’€.,-]*", t))


def guards(page, before=None):
    main = page[page.index('<main id="pn-main">'):page.index("</main>")]
    errs = []
    ids = re.findall(r'<section class="article-section reveal" id="([^"]+)"', main)
    if ids != ORDER:
        errs.append("GR1 sections are %s, expected %s" % (ids, ORDER))
    hero = page[page.index('<header class="d-hero'):page.index("</header>")]
    acts = re.findall(r'<a class="is-(primary|secondary)" href="([^"]+)"', hero)
    if len(acts) != 2 or [a[0] for a in acts] != ["primary", "secondary"]:
        errs.append("GR2 the hero must offer exactly one primary and one secondary action")
    for _, h in acts:
        if not h.startswith("#") or ('id="%s"' % h[1:]) not in page:
            errs.append("GR2 hero action does not reach a section on this page: " + h)
    if re.search(r"check your garden", hero, re.I):
        errs.append("GR2 a 'Check your garden' action would promise a check that does not exist")
    held = HELD_NAME_RE.search(page)
    if held:
        errs.append("GR10 a maker held from the directory is named on the page: " + held.group(0))
    # 30 Oct 2026, founder approval: the Premium Supplier Gallery may show supplier
    # images on this page, ONLY inside its own marker-delimited region, which is
    # held to per-asset rights rules by atlas-tools/prove-supplier-gallery.py.
    # Everywhere else on the page GR3 is unchanged.
    main_wo_gallery = re.sub(r"<!-- PN-SUPPLIER-GALLERY v1 .*?<!-- /PN-SUPPLIER-GALLERY -->", " ", main, flags=re.S)
    if re.search(r'<img[^>]+src="https?://', main_wo_gallery) or "gr-mi-" in page or "what-these-look-like" in page:
        errs.append("GR3 a supplier image or the maker-image section is on the page")
    closed = re.sub(r"<details.*?</details>", " ", main, flags=re.S)
    for need in ("A sauna cabin is a building", "Registered Electrical Contractor",
                 "No Irish supplier we checked publishes a clearance distance",
                 "nothing on this page"):
        if need not in closed:
            errs.append("GR4 essential warning hidden or missing: " + need)
    for d in re.findall(r"<details[^>]*>(.*?)</details>", main, re.S):
        if not d.strip().startswith("<summary"):
            errs.append("GR5 an accordion has no summary")
    words = visible_default(page)
    if words > WORDS_BEFORE * 0.55:
        errs.append("GR6 default view has %d words; must be <= %d" % (words, int(WORDS_BEFORE * 0.55)))
    vis = html.unescape(re.sub(r"<[^>]+>", " ", re.sub(r"<(script|style)\b.*?</\1>|<!--.*?-->", " ",
                                                       main, flags=re.S)))
    g = GOVERNANCE.search(vis)
    if g:
        errs.append("GR7 internal language reaches the reader: " + g.group(0))
    if re.search(r"Irish availability is confirmed for 0", vis + page):
        errs.append("GR8 a count of zero confirmations is shown")
    if before is not None:
        def outside(p):
            p = p[:p.index('<main id="pn-main">')] + p[p.index("</main>"):]
            p = re.sub(r'<div class="d-hero-copy in" id="dHeroCopy">.*?</header>', "", p, flags=re.S)
            p = re.sub(r"/\* PLOTNUA-GR-(MAKER-IMAGERY|RESTRUCTURE)-CSS-BEGIN.*?-CSS-END \*/\n", "", p, flags=re.S)
            return re.sub(r'"dateModified":\s*"[0-9-]+"', "", p)
        if outside(before) != outside(page):
            errs.append("GR9 something outside main, the hero copy, the CSS block or dateModified changed")
    return errs, words


def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "--check"
    src = PAGE.read_text(encoding="utf-8")
    if mode == "--rebuild-from":
        # Re-derive the AFTER page from the pinned BEFORE page in git, so a
        # change to this builder is applied the same way the first build was.
        import subprocess
        rev = sys.argv[2]
        src = subprocess.run(["git", "show", "%s:discovery-garden-retreat.html" % rev], cwd=ROOT,
                             check=True, capture_output=True, text=True).stdout
        mode = "--apply"
    if mode == "--apply":
        out = build(src)
        errs, words = guards(out, before=src)
        if errs:
            die("; ".join(errs))
        PAGE.write_text(out, encoding="utf-8")
        sm = SITEMAP.read_text(encoding="utf-8")
        sm2, n = re.subn(r"(discovery-garden-retreat\.html</loc>\s*<lastmod>)[0-9-]+(</lastmod>)",
                         r"\g<1>%s\2" % TODAY, sm)
        if n != 1:
            die("sitemap entry not found exactly once")
        SITEMAP.write_text(sm2, encoding="utf-8")
        print("Garden Retreat restructure · APPLIED · default view %d words (was %d)" % (words, WORDS_BEFORE))
        return
    if MARK not in src:
        print("Garden Retreat restructure · CHECK: state BEFORE (not yet applied)")
        sys.exit(1)
    errs, words = guards(src)
    if errs:
        print("CHECK FAILED:\n  " + "\n  ".join(errs))
        sys.exit(1)
    print("Garden Retreat restructure · CHECK OK — GR1-GR8, GR10 pass · default view %d words (was %d)"
          % (words, WORDS_BEFORE))


if __name__ == "__main__":
    main()
