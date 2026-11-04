#!/usr/bin/env python3
"""PLOTNUA · DISC-005 Home Exchange: six-chapter editorial restructure (founder approval, 4 Nov 2026).

The page's single article section is split, unchanged, across six chapters; the two photographs move inside
<main> as framed plates between chapters; and:
  - chapter 04 gains the homeowner journey in eight stages, each drawn from facts already on the page and marked
    as what the page establishes or what needs individual confirmation;
  - chapter 05 carries "What a platform does, and what it does not" as a visible block (it was a collapsed
    answer) and the existing Property Check (headline, text and button), moved from the closing panel;
  - chapter 06 is the standard two-route decision (pn-two-route component; route B the existing WhatsApp
    conversation) in the existing closing panel, which keeps its exits and independence line.
No platform, service or partnership is added: the page names none, and this does not either.
Guarded by atlas-tools/prove-premium-discovery-home-exchange.py. Refuses to run twice.

  python3 atlas-tools/build-disc005-editorial.py --apply
"""
import os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = os.path.join(ROOT, "discovery-home-exchange.html")
HEAD_ADD = ('<link rel="stylesheet" href="assets/identity/pn-hx-editorial.css?v=1">\n'
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


def chapter_in_main(n, kicker, title, stand=None, extra=""):
    """main is itself the .article container on this page, so chapter openings are plain wrappers."""
    st = '\n    <p class="lg-stand">%s</p>' % stand if stand else ""
    if title is None:
        return ('<div class="lg-ch-wrap">\n'
                '  <div class="lg-chapter" id="lg-ch%02d"><span class="lg-plot" aria-hidden="true"><span>%02d</span></span>'
                '<p class="lg-kicker">%s</p></div>\n</div>\n' % (n, n, kicker))
    return ('<div class="lg-ch-wrap">\n'
            '  <div class="lg-chapter" id="lg-ch%02d"><span class="lg-plot" aria-hidden="true"><span>%02d</span></span>'
            '<p class="lg-kicker">%s</p></div>\n'
            '  <h2 class="lg-title">%s</h2>%s\n%s</div>\n' % (n, n, kicker, title, st, extra))


STEPS = [
    ("Finding an exchange", "Through a membership platform, which handles the introductions and the profiles. PlotNua does not arrange exchanges.", "Established", "#hx-platform"),
    ("Membership", "You pay the platform an annual membership. No money passes between the two households.", "Established", "#hx-unlocks"),
    ("Matching", "In a straight swap both households have to want the same two weeks. Points or credits mean your dates never have to line up.", "Established", "#hx-routes"),
    ("Dates and expectations", "Agree the fortnight and what is expected on each side; the platform keeps the record of what was agreed.", "Established", "#hx-routes"),
    ("Preparing the house", "Empty a shelf or two, put away what you would rather not have handled, and leave instructions for the heating and the bins.", "Established", "#hx-before"),
    ("Insurance and liability", "Policies commonly restrict cover for an empty house, and whether an exchange counts as occupied is not established. Ask your insurer, in writing.", "Confirm individually", "#hx-before"),
    ("Keys and belongings", "Keys can pass through a neighbour, a lockbox or a key safe. A platform may hold a deposit; read what it actually covers.", "Confirm individually", "#hx-platform"),
    ("Costs and responsibilities", "Mortgage conditions and management-company rules can restrict who may occupy the property, and whether points count as payment is not settled.", "Confirm individually", "#hx-before"),
]


def steps():
    li = "\n".join(
        '    <li><p class="hx-k"><span class="hx-n">%02d</span>%s</p><p class="hx-t">%s</p>'
        '<p class="hx-tag is-%s">%s</p><a class="hx-a" href="%s">The detail</a></li>'
        % (i, s[0], s[1], s[2].lower().replace(" ", "-"), s[2], s[3]) for i, s in enumerate(STEPS, 1))
    return '  <ol class="hx-steps" id="hx-journey" role="list">\n%s\n  </ol>\n' % li


def cut(s, start_marker, end_marker):
    """Return s[start:end] where start is the comment/element at start_marker, end is end_marker's start."""
    i = s.index(start_marker); j = s.index(end_marker, i)
    return s[i:j]


def build(s):
    if 'id="lg-ch01"' in s:
        raise SystemExit("already restructured; refusing to run twice")
    MAIN = '<main class="article" id="pn-main">'
    a = s.index(MAIN); z = s.index('<section class="related reveal">')
    region = s[a:z]
    sec_i = region.index('<section class="article-section reveal">')
    sec = section_at(region, sec_i)
    # the pieces of the one section, in their production order
    head = cut(sec, '<div class="kicker">The Opportunity</div>', "<!-- 1 · QUALIFICATION")
    qual = cut(sec, "<!-- 1 · QUALIFICATION", "<!-- 2 · THE EXCHANGE")
    opp = cut(sec, "<!-- 2 · THE EXCHANGE", "<!-- 3 · THE THREE ROUTES")
    adv = cut(sec, "<!-- 3 · THE THREE ROUTES", "<!-- 4 · BEFORE YOU START")
    before = cut(sec, "<!-- 4 · BEFORE YOU START", '<details class="faq-item is-inline">')
    det = re.findall(r'<details class="faq-item is-inline">.*?</details>', sec, re.S)
    assert len(det) == 3
    d_let, d_fortnight, d_platform = det
    assert "Why this is not letting" in d_let and "fortnight actually" in d_fortnight and "platform does" in d_platform
    rebuilt = head + qual + opp + adv + before + "\n\n    ".join(det)
    assert re.sub(r"\s+", "", rebuilt) in re.sub(r"\s+", "", sec), "the section was not fully accounted for"
    plates = re.findall(r'<section class="imagine-photo reveal">.*?</section>', region, re.S)
    assert len(plates) == 2
    later = [p for p in plates if "991355de2bd66bcc" in p][0]
    bay = [p for p in plates if "7958d59a4ba26f4c" in p][0]
    panel = section_at(region, region.index('<section class="pb-preview reveal" id="discover-your-property">'))

    # the platform answer, made visible (heading once, the answer's own markup unchanged)
    pa = re.search(r'<div class="faq-a">.*?</div>', d_platform, re.S).group(0)
    platform = ('<div class="hx-platform" id="hx-platform">\n      <h3>What a platform does, and what it does not</h3>\n      '
                + pa + "\n    </div>")
    # the Property Check, moved whole from the panel (headline, text, button; the panel's notes kept with it)
    chk_a = panel.index("<!-- PROPERTY BRAIN LAUNCH INTEGRITY")
    chk_z = panel.index('<div class="cs-exits">')
    check = panel[chk_a:chk_z].replace('<div class="pn-wordmark">PlotNua</div>\n', "")
    check = check.replace('<h2 class="pb-headline">', '<h3 class="pb-headline">').replace("own year</h2>", "own year</h3>")
    check = '<div class="hx-check" id="hx-check">\n    ' + check.strip() + "\n    </div>"
    exits = re.search(r'<div class="cs-exits">.*?</div>', panel, re.S).group(0).replace('<div class="cs-exits">', '<div class="cs-exits pd-exits">', 1)
    indep = re.search(r'<p class="pb-independence">.*?</p>', panel, re.S).group(0)

    sect = lambda inner, sid="": ('<section class="article-section reveal"%s>\n    ' % (' id="%s"' % sid if sid else "")) + inner.strip() + "\n  </section>\n"
    plate = lambda p: "  " + p.replace('<section class="imagine-photo reveal">', '<section class="imagine-photo hx-plate reveal">', 1) + "\n\n"

    out = [MAIN + "\n\n"]
    out.append(chapter_in_main(1, "Your home could take you places", None))
    out.append("  " + sect(head))
    out.append(plate(bay))
    out.append(chapter_in_main(2, "Home / Away", "What you lend, and what you borrow.",
                               "On the slider at the top of the page, Home is the house you offer and Away is the home it could be "
                               "exchanged with. The trade is in weeks, not money."))
    out.append("  " + sect(opp + "\n    " + qual, "hx-unlocks"))
    out.append(plate(later))
    out.append(chapter_in_main(3, "Different ways to exchange", "Three ways it can work.",
                               "The arrangements differ in one thing above all: whether both households have to travel at the same time."))
    out.append("  " + sect(adv + "\n    " + d_let, "hx-routes"))
    out.append(chapter_in_main(4, "How does it work?", "From first message to handing back the keys.",
                               "Eight stages, each marked as what this page could establish or what you need to confirm for yourself.",
                               steps()))
    out.append("  " + sect(before + "\n    " + d_fortnight, "hx-before"))
    out.append(chapter_in_main(5, "Finding your next exchange", "Through a platform, on your own terms.",
                               "Exchanges are arranged through membership platforms. PlotNua does not arrange exchanges, rank platforms "
                               "or take a share of anything; check your own year before you pay anybody."))
    out.append("  " + sect(platform + "\n\n    " + check))
    out.append("</main>\n\n")
    out.append('''<!-- CHAPTER 06 (founder approval, 4 Nov 2026): the two-route decision. The Property Check this panel used to
     carry now sits in chapter 05, unchanged; route B is the existing WhatsApp conversation. No form. -->
<section class="pb-preview pd-close reveal" id="discover-your-property" aria-labelledby="hx-routes-h">
  <div class="pd-close-card">
    <div class="lg-chapter" id="lg-ch06"><span class="lg-plot" aria-hidden="true"><span>06</span></span><p class="lg-kicker">Two ways to take the next step</p></div>
    <div class="pn-tr" data-two-route>
    <h2 class="pn-tr-h" id="hx-routes-h">Where could your home take you?</h2>
    <div class="lg-routes">
      <div class="lg-route is-a"><p class="lg-route-l" aria-hidden="true">A</p><p class="lg-route-k">Explore the possibilities yourself</p>
        <p class="lg-route-t">Read how it works and what to settle first, run the Property Check against your own year, then choose a platform directly.</p>
        <ul class="lg-route-links" role="list">
          <li><a href="#hx-routes">Three ways it can work</a></li>
          <li><a href="#hx-journey">How it works, stage by stage</a></li>
          <li><a href="#hx-before">What to settle first</a></li>
          <li><a href="#hx-check">The Property Check</a></li>
          <li><a href="your-plot.html?myplot=1">My Plot: your saved Discoveries</a></li>
        </ul></div>
      <div class="lg-route is-b"><p class="lg-route-l" aria-hidden="true">B</p><p class="lg-route-k">Let PlotNua do the homework</p>
        <p class="lg-route-t">Tell PlotNua about your home and your year, and we&rsquo;ll talk it through with you: which kind of exchange might suit, and what to settle first.</p>
        <div class="pd-btn-row"><a class="pd-btn" href="https://wa.me/353834036695" data-tr-route target="_blank" rel="noopener noreferrer">Chat with PlotNua on WhatsApp<span class="ns-sr"> (opens in a new tab)</span></a></div>
        <p class="lg-free">Free for homeowners.</p>
        <p class="lg-route-n">PlotNua does not arrange exchanges and cannot tell you whether your house will be wanted. Nothing here confirms insurance cover, suitability or any saving.</p></div>
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
        open(PAGE, "w", encoding="utf-8").write(new); print("DISC-005 restructured")
    else:
        print("dry run OK (%d -> %d bytes); pass --apply" % (len(src), len(new)))
