#!/usr/bin/env python3
"""PLOTNUA · DISC-016 Above and Beyond: six-chapter editorial restructure (founder approval, 4 Nov 2026).

Moves the production sections of <main> (unchanged) into six chapters and adds:
  - chapter openings (the Plot Line markers, as DISC-031 / DISC-008);
  - a chapter 02 standfirst, a chapter 04 checklist of the practical considerations, each one drawn
    from facts already on the page and linked to its detail;
  - "Further afield" folded into a closed native <details> (shorter on phones; nothing removed);
  - the Forest Wild / Plan Eden photographs lead the Irish builders (image-led; same credit);
  - chapter 06, the standard two-route decision (pn-two-route component; route B the existing
    WhatsApp conversation), as the closing panel.
Guarded by atlas-tools/prove-premium-discovery-above-and-beyond.py. Refuses to run twice.

  python3 atlas-tools/build-disc016-editorial.py --apply
"""
import os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = os.path.join(ROOT, "discovery-above-and-beyond.html")
HEAD_ADD = ('<link rel="stylesheet" href="assets/identity/pn-ab-editorial.css?v=1">\n'
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
    return ('<div class="article lg-ch-wrap">\n'
            '  <div class="lg-chapter" id="lg-ch%02d"><span class="lg-plot" aria-hidden="true"><span>%02d</span></span>'
            '<p class="lg-kicker">%s</p></div>\n'
            '  <h2 class="lg-title">%s</h2>%s\n%s</div>\n' % (n, n, kicker, title, st, extra))


MAKING = [
    ("Trees and support", "No tree is needed. A structure can stand on its own posts, share the load with a tree, or be carried by one.", "#you-dont-need-a-tree", "Three ways it can stand"),
    ("Tree health", "If a tree is involved, have an arborist look at it before anything is designed. On PlotNua&rsquo;s reading of the professional guidance, the risk near a tree sits mostly in the footings and digging, inside the root protection area. A Tree Preservation Order may also apply.", "#the-evidence", "Trees, safety and insurance"),
    ("Access and safety", "Steps, a ladder or a bridge, and the clear space around them, all take ground. EN&nbsp;1176 does not cover private gardens, so ask a builder which standard, if any, they commit to.", "#practical-questions", "The practical questions"),
    ("Garden size and location", "Garden structures are counted together, nothing of this kind may go forward of the front wall, and private open space to the rear or side must not drop below 25&nbsp;m&sup2;.", "#close-off", "Space, and a future garden house"),
    ("Planning", "Height is the deciding number: usually 3&nbsp;metres overall in the exemption considered here. Only a section&nbsp;5 declaration gives a binding answer.", "#the-one-number", "Why height matters"),
    ("Neighbours", "Overlooking is a design conversation. One published Dublin project sits in the canopy specifically to avoid looking into neighbouring gardens.", "#practical-questions", "Will the neighbours see in?"),
    ("Maintenance and weather", "Ask who services it, how often and at what rate, and what the written structural warranty excludes. Irish makers typically roof these in felt, shingles or steel.", "#the-evidence", "What to get from whoever builds it"),
]


def making_grid():
    li = "\n".join(
        '    <li><p class="ab-mk-k">%s</p><p class="ab-mk-t">%s</p><a class="ab-mk-a" href="%s">%s</a></li>' % m
        for m in MAKING)
    return ('  <ol class="ab-making" id="ab-making" role="list">\n%s\n  </ol>\n' % li)


ROUTES_CLOSE = '''<section class="pb-preview pd-close reveal" id="your-next-step" aria-labelledby="ab-routes-h">
  <div class="pd-close-card">
    <div class="lg-chapter" id="lg-ch06"><span class="lg-plot" aria-hidden="true"><span>06</span></span><p class="lg-kicker">Two ways to take the next step</p></div>
    <div class="pn-tr" data-two-route>
    <h2 class="pn-tr-h" id="ab-routes-h">Choose how you&rsquo;d like to go on.</h2>
    <div class="lg-routes">
      <div class="lg-route is-a"><p class="lg-route-l" aria-hidden="true">A</p><p class="lg-route-k">Explore the possibilities yourself</p>
        <p class="lg-route-t">Read what it can become and what decides whether it works, try the four-question finder, then talk to a maker directly.</p>
        <ul class="lg-route-links" role="list">
          <li><a href="#what-it-can-become">What it can become</a></li>
          <li><a href="#the-one-number">Height and planning</a></li>
          <li><a href="#who-builds-these">Meet the treehouse builders</a></li>
          <li><a href="#your-garden-brief">Find what could work for you</a></li>
          <li><a href="your-plot.html?myplot=1">My Plot: your saved Discoveries</a></li>
        </ul></div>
      <div class="lg-route is-b"><p class="lg-route-l" aria-hidden="true">B</p><p class="lg-route-k">Let PlotNua do the homework</p>
        <p class="lg-route-t">Tell PlotNua about your garden and what you&rsquo;d like up there, and we&rsquo;ll talk it through with you, using what PlotNua has researched about makers, height and planning.</p>
        <div class="pd-btn-row"><a class="pd-btn" href="https://wa.me/353834036695" data-tr-route target="_blank" rel="noopener noreferrer">Chat with PlotNua on WhatsApp<span class="ns-sr"> (opens in a new tab)</span></a></div>
        <p class="lg-free">Free for homeowners.</p>
        <p class="lg-route-n">PlotNua doesn&rsquo;t design or build these, and can&rsquo;t confirm planning status, structural safety or whether a tree or garden is suitable. Nothing is booked by starting a conversation.</p></div>
    </div>
    </div>
  </div>
</section>

'''


def build(s):
    if 'id="lg-ch01"' in s:
        raise SystemExit("already restructured; refusing to run twice")
    a = s.index('<main id="pn-main">'); z = s.index("</main>") + len("</main>")
    m = s[a:z]
    lookup = by_id(m, "look-up")
    annot = by_id(m, "whats-above-your-garden"); annot_c = comment_before(m, annot)
    notree = by_id(m, "you-dont-need-a-tree")
    pod = by_img(m, "assets/img/55f2bd4248ec234f.jpg"); pod_c = comment_before(m, pod)
    inside = by_img(m, "assets/img/6417da715bd0aabc.jpg"); inside_c = comment_before(m, inside)
    become = by_id(m, "what-it-can-become")
    market = by_id(m, "the-market-stops")
    height = by_id(m, "the-one-number")
    close = by_id(m, "close-off")
    faq = by_id(m, "practical-questions")
    who = by_id(m, "who-builds-these")
    brief = by_id(m, "your-garden-brief")
    evid = by_id(m, "the-evidence")
    # every section of <main> must be accounted for
    allsec = re.findall(r"<section\b", m)
    used = [lookup, annot, notree, pod, inside, become, market, height, close, faq, who, brief, evid]
    nested = sum(len(re.findall(r"<section\b", u)) for u in used)
    assert nested == len(allsec), (nested, len(allsec))

    # chapter 05: Forest Wild photographs lead the Irish builders; "Further afield" folds into <details>
    fw_i = who.index('<div class="map-one has-photos">')
    fw_end = who.index("</div>\n    </div>\n    <h3 class=\"map-band is-afield\"")
    fw = who[fw_i:fw_end + len("</div>")]
    who2 = who.replace(fw, "", 1)
    who2 = who2.replace('<div class="map-set">\n', '<div class="map-set">\n      ' + fw.strip() + "\n", 1)
    af_a = who2.index('<h3 class="map-band is-afield">')
    af_z = who2.rindex("</section>")
    afield = who2[af_a:af_z].rstrip()
    who2 = (who2[:af_a] + '<details class="ab-afield" id="ab-afield">\n      <summary>Further afield: five specialists outside Ireland</summary>\n      '
            + afield + "\n    </details>\n  " + who2[af_z:])

    art = lambda *x: '<div class="article">\n\n  ' + "\n\n  ".join(x) + "\n\n</div>\n"
    out = ['<main id="pn-main">\n']
    out.append(chapter(1, "The possibility", "A space above the ordinary garden."))
    out.append(art(lookup))
    out.append("\n  " + annot_c + annot + "\n\n")
    out.append(chapter(2, "A different perspective", "The garden, seen from the canopy.",
                       "Lifted even a metre or two, the same garden looks different: you see over the hedge, into the "
                       "branches, and back at the house. The ground stays where it was; what changes is where you stand."))
    out.append("  " + inside_c + inside + "\n\n")
    out.append(art(notree))
    out.append("\n  " + pod_c + pod + "\n\n")
    out.append(chapter(3, "More than a treehouse", "One idea, many uses.",
                       "A den, a play structure, a quiet retreat, a games room or a studio. Not every structure suits every use, "
                       "and none of them is somewhere to live."))
    out.append(art(become))
    out.append(chapter(4, "Making it possible", "What decides whether it works.",
                       "Seven things to think through before anything is ordered, each with its detail on this page.",
                       making_grid()))
    out.append(art(height, close, faq))
    out.append(chapter(5, "Meet the treehouse builders", "Who builds these in Ireland.",
                       "Published prices first, then the makers, then a four-question finder that points you to the ones that fit."))
    out.append(art(market, who2, brief, evid))
    out.append("</main>")
    s = s[:a] + "".join(out) + s[z:]
    rel = '<section class="related reveal">'
    assert s.count(rel) == 1
    s = s.replace(rel, ROUTES_CLOSE + rel, 1)
    assert s.count("</head>") == 1
    s = s.replace("</head>", HEAD_ADD + "</head>", 1)
    return s


if __name__ == "__main__":
    src = open(PAGE, encoding="utf-8").read()
    new = build(src)
    if "--apply" in sys.argv:
        open(PAGE, "w", encoding="utf-8").write(new); print("DISC-016 restructured")
    else:
        print("dry run OK (%d -> %d bytes); pass --apply" % (len(src), len(new)))
