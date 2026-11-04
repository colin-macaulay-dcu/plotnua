#!/usr/bin/env python3
"""PLOTNUA · DISC-025 The Borrowed Garden: six-chapter editorial restructure (founder approval, 4 Nov 2026:
EDITORIAL MAKEOVER ONLY).

Moves the production sections of <main> (unchanged) into six chapters and adds chapter openings, a chapter 03
list of what could grow here (each line drawn from the page's own facts, or stated as not arranged), and chapter
06, the two-route decision (pn-two-route component; route B the existing WhatsApp conversation only).

REGISTER RULE. The Garden Owner and Grower registers are not touched. The closing panel's existing "Two ways to
take part" block (the two existing check links, the three stages and the note) moves, byte for byte, into
chapter 05; no link to a check or register is added anywhere, and chapter 06 invites no registration. The
check pages, the register Worker and every stored record are outside this change.
Guarded by atlas-tools/prove-premium-discovery-borrowed-garden.py. Refuses to run twice.

  python3 atlas-tools/build-disc025-editorial.py --apply
"""
import os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = os.path.join(ROOT, "discovery-the-borrowed-garden.html")
HEAD_ADD = ('<link rel="stylesheet" href="assets/identity/pn-bg-editorial.css?v=1">\n'
            '<link rel="stylesheet" href="assets/components/pn-two-route.css?v=1">\n')


def section_at(s, i):
    """Return the full <section ...>...</section> starting at index i (sections may nest)."""
    assert s.startswith("<section", i)
    depth, j = 0, i
    for m in re.compile(r"<section\b|</section>").finditer(s, i):
        depth += 1 if m.group(0) == "<section" else -1
        if depth == 0:
            return s[i:m.end()]
    raise ValueError("unbalanced section")


def by_id(s, sid):
    i = s.rfind("<section", 0, s.index('id="%s"' % sid))
    return section_at(s, i)


def by_img(s, src):
    i = s.rfind("<section", 0, s.index('src="%s"' % src))
    return section_at(s, i)


def comment_before(s, sec):
    """The HTML comment immediately preceding a section, kept with it."""
    i = s.index(sec)
    pre = s[:i].rstrip()
    if pre.endswith("-->"):
        j = pre.rfind("<!--")
        return s[j:i]
    return ""


def chapter(n, kicker, title, stand=None, extra=""):
    st = '\n    <p class="lg-stand">%s</p>' % stand if stand else ""
    if title is None:
        return ('<div class="article lg-ch-wrap">\n'
                '  <div class="lg-chapter" id="lg-ch%02d"><span class="lg-plot" aria-hidden="true"><span>%02d</span></span>'
                '<p class="lg-kicker">%s</p></div>\n</div>\n' % (n, n, kicker))
    return ('<div class="article lg-ch-wrap">\n'
            '  <div class="lg-chapter" id="lg-ch%02d"><span class="lg-plot" aria-hidden="true"><span>%02d</span></span>'
            '<p class="lg-kicker">%s</p></div>\n'
            '  <h2 class="lg-title">%s</h2>%s\n%s</div>\n' % (n, n, kicker, title, st, extra))


GROW = [
    ("Vegetables", "A raised bed or two, with a share of the harvest the commonest arrangement.", "#bg-settle"),
    ("Growing side by side", "You keep using the garden and it stays your garden; the grower works the part you chose.", "#bg-agree"),
    ("Community growing", "People already look for ground through community gardens, local growing groups and council lists, and some council lists are full.", "#bg-sharing"),
    ("Supported gardening", "Some people may want to grow with help. Nothing of that kind is arranged here; supervision and safeguarding would have to be agreed first.", "#bg-agree"),
    ("Neighbours", "The grower may live a few streets away. Neither of you currently knows the other exists.", "#bg-sharing"),
]


def grow():
    li = "\n".join('    <li><p class="bg-k">%s</p><p class="bg-t">%s</p><a class="bg-a" href="%s">Read more</a></li>' % g for g in GROW)
    return '  <ul class="bg-grow" id="bg-grow" role="list">\n%s\n  </ul>\n' % li


def cut(s, start_marker, end_marker=None):
    i = s.index(start_marker)
    j = s.index(end_marker, i) if end_marker else len(s)
    return s[i:j]


def build(s):
    if 'id="lg-ch01"' in s:
        raise SystemExit("already restructured; refusing to run twice")
    a = s.index('<main id="pn-main">'); z = s.index('<section class="related reveal">')
    region = s[a:z]
    secs = []
    i = 0
    while True:
        j = region.find('<section class="article-section reveal">', i)
        if j < 0: break
        sec = section_at(region, j); secs.append(sec); i = j + len(sec)
    assert len(secs) == 4, len(secs)
    s1, s2, s3, s4 = secs
    assert "The Opportunity" in s1 and "Before You Agree" in s2 and "And afterwards" in s3 and "Where this could go" in s4
    inner1 = s1[s1.index(">") + 1: s1.rindex("</section>")]
    head = cut(inner1, '<div class="kicker">The Opportunity</div>', "<!-- 1 · THE CONTRAST")
    contrast = cut(inner1, "<!-- 1 · THE CONTRAST", "<!-- 2 · HOW IT WORKS")
    settle = cut(inner1, "<!-- 2 · HOW IT WORKS")
    assert re.sub(r"\s+", "", head + contrast + settle) == re.sub(r"\s+", "", inner1)
    px = re.search(r"<!-- PLOTNUA-PROVIDER-EXPLORER-V1 · BEGIN.*?PLOTNUA-PROVIDER-EXPLORER-V1 · END -->", region, re.S).group(0)
    plates = re.findall(r'<section class="imagine-photo[^"]*">.*?</section>', region, re.S)
    assert len(plates) == 3
    p_asset, p_grower, p_outcome = (next(p for p in plates if k in p) for k in ("59d566ff7c3a50e8", "75f721f0513e4f37", "ba3fbcc7a04da889"))
    panel = section_at(region, region.index('<section class="pb-preview reveal" id="discover-your-property">'))
    take = panel[panel.index("<!-- CLOSING JOURNEY PANEL"):panel.index('<div class="cs-exits">')]
    exits = re.search(r'<div class="cs-exits">.*?</div>', panel, re.S).group(0).replace('<div class="cs-exits">', '<div class="cs-exits pd-exits">', 1)
    indep = re.search(r'<p class="pb-independence">.*?</p>', panel, re.S).group(0)
    # every piece of <main> and the panel is accounted for
    used = [s1, s2, s3, s4, px] + plates
    assert sum(len(re.findall(r"<section\b", u)) for u in used) == len(re.findall(r"<section\b", region[:region.index("</main>")]))

    sect = lambda inner, sid="": ('<section class="article-section reveal"%s>\n    ' % (' id="%s"' % sid if sid else "")) + inner.strip() + "\n  </section>"
    s2i = s2.replace('<section class="article-section reveal">', '<section class="article-section reveal" id="bg-agree">', 1)
    s4i = s4.replace('<section class="article-section reveal">', '<section class="article-section reveal" id="bg-future">', 1)
    art = lambda *x: '<div class="article">\n\n  ' + "\n\n  ".join(x) + "\n\n</div>\n"
    out = ['<main id="pn-main">\n']
    out.append(chapter(1, "The garden you already have", None))
    out.append(art(sect(head)))
    out.append("\n" + p_asset + "\n\n")
    out.append(chapter(2, "A different kind of sharing", "Your ground, their growing.",
                       "Two people, two sides: somebody with ground they barely use, and somebody nearby without any."))
    out.append(art(sect(contrast, "bg-sharing")))
    out.append(chapter(3, "What could grow here?", "More than a vegetable bed.",
                       "What a shared corner could become. None of these is a PlotNua service or an existing programme.",
                       grow()))
    out.append("\n" + p_grower + "\n\n")
    out.append(art(s3))
    out.append("\n" + p_outcome + "\n\n")
    out.append(chapter(4, "Making it work responsibly", "Settle it before anyone starts.",
                       "Which part, access, insurance, money, what is written down and how it ends are agreed before any growing "
                       "begins. Where children or vulnerable adults would be involved, safeguarding needs its own arrangements, "
                       "which this page does not cover."))
    out.append(art(sect(settle, "bg-settle"), s2i))
    out.append(chapter(5, "The possibility of a shared garden", "What exists, and what does not yet.",
                       "Organisations already working on this, what PlotNua is exploring, and the two short checks. "
                       "No arrangement has been made through PlotNua: the pictures on this page show the idea, not a real one."))
    out.append(art(px, s4i, '<div class="bg-checks pb-preview" id="bg-checks">\n    ' + take.strip() + "\n  </div>"))
    out.append("</main>\n\n")
    out.append('''<!-- CHAPTER 06 (founder approval, 4 Nov 2026: editorial makeover only). The two-route decision. Route B is the
     existing WhatsApp conversation and nothing else: it registers nobody, matches nobody and introduces nobody.
     The existing "Two ways to take part" block now sits in chapter 05, unchanged. -->
<section class="pb-preview pd-close reveal" id="discover-your-property" aria-labelledby="bg-routes-h">
  <div class="pd-close-card">
    <div class="lg-chapter" id="lg-ch06"><span class="lg-plot" aria-hidden="true"><span>06</span></span><p class="lg-kicker">Two ways to take the next step</p></div>
    <div class="pn-tr" data-two-route>
    <h2 class="pn-tr-h" id="bg-routes-h">Curious whether it could work for you?</h2>
    <div class="lg-routes">
      <div class="lg-route is-a"><p class="lg-route-l" aria-hidden="true">A</p><p class="lg-route-k">Explore the idea yourself</p>
        <p class="lg-route-t">Read what to settle first and who is already working on this, then decide whether it is for you.</p>
        <ul class="lg-route-links" role="list">
          <li><a href="#bg-sharing">Your ground, their growing</a></li>
          <li><a href="#bg-settle">Six things to settle</a></li>
          <li><a href="#bg-agree">Before you agree</a></li>
          <li><a href="#explore-providers">Organisations already doing this</a></li>
          <li><a href="your-plot.html?myplot=1">My Plot: your saved Discoveries</a></li>
        </ul></div>
      <div class="lg-route is-b"><p class="lg-route-l" aria-hidden="true">B</p><p class="lg-route-k">Ask PlotNua about The Borrowed Garden</p>
        <p class="lg-route-t">Ask PlotNua about the idea and your garden, and we&rsquo;ll talk it through with you, using what PlotNua has researched.</p>
        <div class="pd-btn-row"><a class="pd-btn" href="https://wa.me/353834036695" data-tr-route target="_blank" rel="noopener noreferrer">Chat with PlotNua on WhatsApp<span class="ns-sr"> (opens in a new tab)</span></a></div>
        <p class="lg-free">Free for homeowners.</p>
        <p class="lg-route-n">The Borrowed Garden is an idea PlotNua is still exploring, not a service. Starting a conversation signs you up to nothing, and nobody is put in touch with anybody.</p></div>
    </div>
    </div>
    ''' + exits + "\n    " + indep + "\n  </div>\n</section>\n\n")
    s = s[:a] + "".join(out) + s[z:]
    assert s.count("</head>") == 1
    s = s.replace("</head>", HEAD_ADD + "</head>", 1)
    return s


if __name__ == "__main__":
    src = open(PAGE, encoding="utf-8").read()
    new = build(src)
    if "--apply" in sys.argv:
        open(PAGE, "w", encoding="utf-8").write(new); print("DISC-025 restructured")
    else:
        print("dry run OK (%d -> %d bytes); pass --apply" % (len(src), len(new)))
