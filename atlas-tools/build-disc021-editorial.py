#!/usr/bin/env python3
"""PLOTNUA · DISC-021 Your Home On Screen: six-chapter editorial restructure (founder approval, 4 Nov 2026).

Moves the production sections of <main> (unchanged) into six chapters and adds:
  - chapter openings (the Plot Line markers, as DISC-016 / DISC-031);
  - chapter 03, the uses, each line drawn from facts already on the page;
  - chapter 04, the homeowner journey in eight steps, each marked as what the page establishes or what it
    could not establish, drawn from the page's own sections and linked to them;
  - chapter 06, the standard two-route decision (pn-two-route component; route B the existing WhatsApp
    conversation), in the existing closing panel, replacing its "property check is being prepared"
    placeholder copy (as DISC-001). The panel's exits and independence line stay.
Guarded by atlas-tools/prove-premium-discovery-your-home-on-screen.py. Refuses to run twice.

  python3 atlas-tools/build-disc021-editorial.py --apply
"""
import os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = os.path.join(ROOT, "discovery-your-home-on-screen.html")
HEAD_ADD = ('<link rel="stylesheet" href="assets/identity/pn-ys-editorial.css?v=1">\n'
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


USES = [
    ("Advertising and content", "The busiest end of the Irish market: shoots for advertising agencies and content creators, often a smaller crew for a day.", "#where-ireland-stands"),
    ("Television", "Drama and series, including shows set in the UK or America, where an ordinary Irish house can stand in for a house somewhere else.", "#what-they-look-for"),
    ("Film", "Television drama and feature films use homes too, and on bigger productions there can be up to 200 people on set.", "#what-it-involves"),
    ("Stills photography", "Stills photography is part of the Irish demand too, alongside television, advertising and content.", "#the-revelation"),
]


def uses():
    li = "\n".join('    <li><p class="ys-k">%s</p><p class="ys-t">%s</p><a class="ys-a" href="%s">Read more</a></li>' % u for u in USES)
    return '  <ul class="ys-uses" id="ys-uses" role="list">\n%s\n  </ul>\n' % li


STEPS = [
    ("Initial enquiry", "It may start with your listing, a local film office, or a letter through the door from a location manager who has chosen your street.", "Established", "#how-it-happens"),
    ("Location assessment", "There can be several visits from crew before anyone decides whether to use your home at all. It might go nowhere.", "Established", "#what-it-involves"),
    ("Property photographs", "The national register asks for as much detail and as many images as you can give it.", "Established", "#where-ireland-stands"),
    ("Suitability and access", "Parking, a way in for equipment, dry storage, power and toilets usually decide it, more than how the house looks.", "Established", "#what-they-look-for"),
    ("Scheduling", "From an afternoon to twelve weeks in one Irish example, including set-up and removal. You say when the property is not available.", "Established", "#what-it-involves"),
    ("Agreements and permissions", "Changes are agreed line by line, rooms can be put out of bounds, and you sign a contract. Tenants and joint owners should settle authorisation first.", "Established", "#practical-questions"),
    ("Insurance and arrangements", "How household insurance treats filming is not established: check with your insurer first. You may be asked to move out for the duration.", "Not established", "#practical-questions"),
    ("Payment", "Fees are negotiated directly, and there is no Irish day rate. Agency commission is not published, and the tax treatment of a fee is a question for Revenue.", "Varies", "#the-money"),
]


def steps():
    li = "\n".join(
        '    <li><p class="ys-k"><span class="ys-n">%02d</span>%s</p><p class="ys-t">%s</p>'
        '<p class="ys-tag is-%s">%s</p><a class="ys-a" href="%s">The detail</a></li>'
        % (i, s[0], s[1], s[2].lower().replace(" ", "-"), s[2], s[3]) for i, s in enumerate(STEPS, 1))
    return '  <ol class="ys-steps" id="ys-steps" role="list">\n%s\n  </ol>\n' % li


def close_panel(old):
    exits = re.search(r'<div class="cs-exits">.*?</div>', old, re.S).group(0)
    indep = re.search(r'<p class="pb-independence">.*?</p>', old, re.S).group(0)
    exits = exits.replace('<div class="cs-exits">', '<div class="cs-exits pd-exits">', 1)
    return '''<section class="pb-preview pd-close reveal" id="discover-your-property" aria-labelledby="ys-routes-h">
  <div class="pd-close-card">
    <div class="lg-chapter" id="lg-ch06"><span class="lg-plot" aria-hidden="true"><span>06</span></span><p class="lg-kicker">Two ways to take the next step</p></div>
    <div class="pn-tr" data-two-route>
    <h2 class="pn-tr-h" id="ys-routes-h">Curious whether your home could work?</h2>
    <div class="lg-routes">
      <div class="lg-route is-a"><p class="lg-route-l" aria-hidden="true">A</p><p class="lg-route-k">Explore the possibilities yourself</p>
        <p class="lg-route-t">Read what productions look for and what really happens, then register or list your home directly.</p>
        <ul class="lg-route-links" role="list">
          <li><a href="#what-they-look-for">What productions look for</a></li>
          <li><a href="#what-it-involves">What actually happens</a></li>
          <li><a href="#the-money">What you might be paid</a></li>
          <li><a href="#how-it-happens">How a home gets found</a></li>
          <li><a href="your-plot.html?myplot=1">My Plot: your saved Discoveries</a></li>
        </ul></div>
      <div class="lg-route is-b"><p class="lg-route-l" aria-hidden="true">B</p><p class="lg-route-k">Let PlotNua do the homework</p>
        <p class="lg-route-t">Tell PlotNua about your home and we&rsquo;ll talk it through with you: the practical questions productions ask, and where to register or list.</p>
        <div class="pd-btn-row"><a class="pd-btn" href="https://wa.me/353834036695" data-tr-route target="_blank" rel="noopener noreferrer">Chat with PlotNua on WhatsApp<span class="ns-sr"> (opens in a new tab)</span></a></div>
        <p class="lg-free">Free for homeowners.</p>
        <p class="lg-route-n">PlotNua is not a location agency and does not put properties forward. Nothing here assesses your property or means it will be used, and no fee is promised.</p></div>
    </div>
    </div>
    ''' + exits + "\n    " + indep + "\n  </div>\n</section>"


def build(s):
    if 'id="lg-ch01"' in s:
        raise SystemExit("already restructured; refusing to run twice")
    a = s.index('<main id="pn-main">'); z = s.index("</main>") + len("</main>")
    m = s[a:z]
    rev = by_id(m, "the-revelation")
    annot = by_id(m, "what-a-production-sees"); annot_c = comment_before(m, annot)
    see = by_id(m, "what-they-see")
    ireland = by_id(m, "where-ireland-stands")
    look = by_id(m, "what-they-look-for")
    how = by_id(m, "how-it-happens")
    room = by_img(m, "assets/img/7f49094747879fe4.jpg"); room_c = comment_before(m, room)
    inv = by_id(m, "what-it-involves")
    shoot = by_img(m, "assets/img/80614bf6b2d7d79a.jpg"); shoot_c = comment_before(m, shoot)
    money = by_id(m, "the-money")
    faq = by_id(m, "practical-questions")
    ahead = by_id(m, "looking-ahead")
    evid = by_id(m, "the-evidence")
    used = [rev, annot, see, ireland, look, how, room, inv, shoot, money, faq, ahead, evid]
    assert sum(len(re.findall(r"<section\b", u)) for u in used) == len(re.findall(r"<section\b", m))

    art = lambda *x: '<div class="article">\n\n  ' + "\n\n  ".join(x) + "\n\n</div>\n"
    out = ['<main id="pn-main">\n']
    out.append(chapter(1, "Your home could be the set", None))
    out.append(art(rev))
    out.append("\n  " + annot_c + annot + "\n\n")
    out.append(chapter(2, "What makes a home interesting?", "Character and practicality, not polish.",
                       "Interiors with personality, architecture that could pass for somewhere else, a driveway with room for a van. "
                       "None of these guarantees interest; together they are what the people who find locations describe looking for."))
    out.append(art(see, look))
    out.append(chapter(3, "What could your home be used for?", "Not only film.",
                       "Most Irish demand is not feature film. These are the kinds of production the page&rsquo;s sources describe.",
                       uses()))
    out.append("  " + room_c + room + "\n\n")
    out.append(chapter(4, "How does it actually work?", "From the first letter to the last van.",
                       "Eight stages, each marked as what this page could establish and what it could not.",
                       steps()))
    out.append(art(inv))
    out.append("\n  " + shoot_c + shoot + "\n\n")
    out.append(art(money, faq))
    out.append(chapter(5, "Finding the right people", "Registers, film offices and platforms.",
                       "Most of it is free to join. None of these organisations has any arrangement with PlotNua."))
    out.append(art(ireland, how, ahead, evid))
    out.append("</main>")
    s = s[:a] + "".join(out) + s[z:]
    i = s.index('<section class="pb-preview reveal" id="discover-your-property">')
    old = section_at(s, i)
    s = s.replace(old, close_panel(old), 1)
    c0 = s.rfind("<!--", 0, s.index('id="discover-your-property"'))
    c1 = s.index("-->", c0) + 3
    assert "PROPERTY BRAIN" in s[c0:c1]
    s = s[:c0] + ("<!-- CHAPTER 06 (founder approval, 4 Nov 2026): the two-route decision replaces the earlier\n"
                  "     'property check is being prepared' placeholder in this panel. Route B is the existing WhatsApp\n"
                  "     conversation; no form, no Eircode input, no property assessment. -->") + s[c1:]
    assert s.count("</head>") == 1
    s = s.replace("</head>", HEAD_ADD + "</head>", 1)
    return s


if __name__ == "__main__":
    src = open(PAGE, encoding="utf-8").read()
    new = build(src)
    if "--apply" in sys.argv:
        open(PAGE, "w", encoding="utf-8").write(new); print("DISC-021 restructured")
    else:
        print("dry run OK (%d -> %d bytes); pass --apply" % (len(src), len(new)))
