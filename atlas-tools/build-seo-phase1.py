#!/usr/bin/env python3
"""
SEO PHASE 1 · founder-approved 16 Oct 2026 (bounded build, existing pages only)
==============================================================================
Applies the on-page changes for the four priority Discoveries plus two
site-level fixes. Every edit is an exact, single-occurrence replacement on the
page's current text; if an anchor is missing or ambiguous the builder refuses
and writes nothing. Run twice and the second run changes nothing.

  python3 atlas-tools/build-seo-phase1.py           apply
  python3 atlas-tools/build-seo-phase1.py --check   verify applied, write nothing

WHAT IT CHANGES
  * <title> and meta description (the page's search snippet) for:
      Living in the Garden, Garden Retreat, Hidden Bins, Driveway Income.
    Social (og:/twitter:) titles are deliberately left as they are: they are
    the editorial voice and are not what Google shows in results.
  * One short "In brief" section at the top of each article. Every fact in it
    is already stated further down the same page; nothing new is claimed.
  * A small number of H2s gain the words people search with, keeping voice.
    Frozen / builder-owned headings (Garden Retreat restructure anchors,
    Hidden Bins frozen copy) are NOT touched.
  * Contextual links: Living in the Garden <-> Garden Retreat (in the brief),
    Driveway Income -> Hidden Bins (in the brief).
  * JSON-LD: WebPage + BreadcrumbList (+ WebSite / Organization) on all four.
    Hidden Bins and Driveway Income had none. No FAQPage: Google has shown FAQ
    rich results only for well-known government and health sites since 2023,
    and the visible FAQs are collapsible editorial prose; marking them up
    would add weight without a supported result.
  * Hero LCP: <link rel="preload" as="image" fetchpriority="high"> for the
    image the page already paints first. No image file is added or changed.
  * search.html: robots "noindex, follow" and removed from sitemap.xml (a
    sitemap entry asserts "index this", same rule as your-plot.html).

WHAT IT DOES NOT TOUCH
  Atlas data, Workers, product classifications, supplier claims, imagery,
  credits, the image-rights manifest, the Garden Owner and Grower journeys.
"""
import re
import sys
import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
CHECK = "--check" in sys.argv
TODAY = "2026-10-16"
# Garden Retreat's own dateModified, following its real content changes so it agrees with its sitemap
# lastmod (cluster 2 guard S2). 22 Oct 2026: the commercial disclosure (TimberIN referral code) changed.
GR_MODIFIED = "2026-10-22"
# Living in the Garden's own dateModified. It follows the page's real content
# changes, so it agrees with its sitemap lastmod (cluster 1 guard S2).
# 17 Oct 2026: two factual corrections (commencement date; An Coimisiun Pleanala).
# 19 Oct 2026: the safety hold removed the five Premium Log House products from the Maker Explorer
# 20 Oct 2026: the Outdoor Living correction moved the Maker Explorer counts
# 26 Oct 2026: buying guidance and contextual links, with research figures unchanged.
LITG_MODIFIED = "2026-10-26"


def die(msg):
    print("REFUSED: " + msg + " -- nothing written")
    sys.exit(1)


def jsonld(slug, name, desc, crumb, img):
    u = "https://plotnua.ie/%s.html" % slug
    return (
        '<script type="application/ld+json">\n'
        '{\n'
        '  "@context": "https://schema.org",\n'
        '  "@graph": [\n'
        '    {\n'
        '      "@type": "WebPage",\n'
        '      "@id": "%s#webpage",\n'
        '      "url": "%s",\n'
        '      "name": "%s",\n'
        '      "description": "%s",\n'
        '      "inLanguage": "en-IE",\n'
        '      "dateModified": "%s",\n'
        '      "primaryImageOfPage": { "@type": "ImageObject", "url": "https://plotnua.ie/%s" },\n'
        '      "isPartOf": { "@id": "https://plotnua.ie/#website" },\n'
        '      "publisher": { "@id": "https://plotnua.ie/#organisation" },\n'
        '      "breadcrumb": { "@id": "%s#breadcrumb" }\n'
        '    },\n'
        '    {\n'
        '      "@type": "BreadcrumbList",\n'
        '      "@id": "%s#breadcrumb",\n'
        '      "itemListElement": [\n'
        '        { "@type": "ListItem", "position": 1, "name": "PlotNua", "item": "https://plotnua.ie/" },\n'
        '        { "@type": "ListItem", "position": 2, "name": "Discoveries", "item": "https://plotnua.ie/discoveries.html" },\n'
        '        { "@type": "ListItem", "position": 3, "name": "%s" }\n'
        '      ]\n'
        '    },\n'
        '    {\n'
        '      "@type": "WebSite",\n'
        '      "@id": "https://plotnua.ie/#website",\n'
        '      "url": "https://plotnua.ie/",\n'
        '      "name": "PlotNua",\n'
        '      "inLanguage": "en-IE",\n'
        '      "publisher": { "@id": "https://plotnua.ie/#organisation" }\n'
        '    },\n'
        '    {\n'
        '      "@type": "Organization",\n'
        '      "@id": "https://plotnua.ie/#organisation",\n'
        '      "name": "PlotNua",\n'
        '      "url": "https://plotnua.ie/"\n'
        '    }\n'
        '  ]\n'
        '}\n'
        '</script>\n'
    ) % (u, u, name, desc, TODAY, img, u, u, crumb)


def brief(paragraph):
    return (
        '\n  <!-- SEO PHASE 1 (16 Oct 2026) · IN BRIEF. Every fact here is stated\n'
        '       further down this page; this only puts the answer first. -->\n'
        '  <section class="article-section pn-brief" aria-label="In brief" style="padding-bottom:28px">\n'
        '    <div class="kicker">In Brief</div>\n'
        '    <p style="max-width:68ch">%s</p>\n'
        '  </section>\n' % paragraph
    )


def preload(img):
    return ('<link rel="preload" as="image" href="%s" fetchpriority="high">\n' % img)


# ---------------------------------------------------------------- the edits
# (file, [(old, new), ...]) -- old must occur exactly once (or new already
# present, in which case the edit is already applied).

LITG_IMG = "assets/img/8c60a8f27eb9c697.jpg"
GR_IMG = "assets/img/7d5f5718cf9cd3da.jpg"
HB_IMG = "assets/img/9805382f8164228a.jpg"
DI_IMG = "assets/img/b5cbac3fff9072d4.jpg"
HOME_IMG = "assets/img/9785fd991d2488e9.jpg"
PHASE4_REVEAL_PRELOAD = ('<link rel="preload" as="image" type="image/avif" '
                         'imagesrcset="assets/possibility-reveal/img/house-L1-L2A-1376.avif 1376w, ')
# H6 (26 Oct 2026) replaces the Possibility Reveal: the homepage LCP is the H6 empty
# garden, preloaded as AVIF from the component's own encodings (build-h6-homepage.py).
H6_PRELOAD = ('<link rel="preload" as="image" type="image/avif" '
              'imagesrcset="assets/h6/img/H6-garden-base-v6-960.avif 960w, ')

# SEO-C1.3 (20 Oct 2026): the description serves the page's commercial role as
# well as planning (founder-approved wording). LITG_DESC_V1 is the 16 Oct text
# it replaces; the transition edits below move a page that still carries it.
LITG_DESC_V1 = ("Since July 2026 an Irish garden room can be up to 30 m&sup2; and a garden "
                "home 32&ndash;45 m&sup2; without a planning application. The conditions, explained.")
LITG_DESC = ("Garden rooms, garden offices and garden homes in Ireland: the makers PlotNua has "
             "researched, what advertised prices cover, and the 2026 planning rules.")
# The same words in the WebPage structured data (plain ASCII, so no JSON escaping).
LITG_DESC_LD = LITG_DESC
assert "&" not in LITG_DESC_LD and '"' not in LITG_DESC_LD
GR_DESC = ("Garden saunas, hot tubs and cold plunges in Ireland: real published prices, "
           "the space each needs, and how the 30 m&sup2; and 25 m&sup2; limits apply.")
HB_DESC = ("Three ways to hide wheelie bins at an Irish home, from bin stores to underground "
           "lifts: what is available in Ireland, costs and the 2026 planning change.")
DI_DESC = ("Could your driveway earn money from parking? What Irish homeowners report, "
           "how tax and insurance apply, and what planning law does not yet settle.")

EDITS = {
    "discovery-living-in-the-garden.html": [
        # SEO-C1.3 transition (20 Oct 2026): the 16 Oct description -> the current one,
        # in the meta tag and in the WebPage structured data. Applied first, so the
        # edits below then find their replacements already in place.
        ('<meta name="description" content="%s">' % LITG_DESC_V1,
         '<meta name="description" content="%s">' % LITG_DESC),
        ('      "description": "Since July 2026 an Irish garden room can be up to 30 m\\u00b2 and a garden '
         'home 32\\u201345 m\\u00b2 without a planning application. The conditions, explained.",\n',
         '      "description": "%s",\n' % LITG_DESC_LD),
        ("<title>Garden Rooms &amp; Garden Homes in Ireland: 2026 Planning Rules | PlotNua</title>",
         "<title>Garden Rooms &amp; Garden Homes in Ireland | PlotNua</title>"),
        ('<meta name="description" content="What the July 2026 regulations changed: the 30 m² garden room, '
         'the new 32–45 m² garden home, what counts towards the limit — and the separate 25 m² Building '
         'Regulations threshold almost nobody mentions.">',
         '<meta name="description" content="%s">' % LITG_DESC),
        ('<link rel="canonical" href="https://plotnua.ie/discovery-living-in-the-garden.html">\n',
         '<link rel="canonical" href="https://plotnua.ie/discovery-living-in-the-garden.html">\n'
         + preload(LITG_IMG)),
        ('"name": "Garden Rooms & Garden Homes in Ireland: 2026 Planning Rules",\n'
         '      "description": "What the July 2026 regulations changed: the 30 m\\u00b2 garden room, the new '
         '32\\u201345 m\\u00b2 garden home, and what counts towards the limit.",\n'
         '      "inLanguage": "en-IE",\n'
         '      "dateModified": "2026-10-11",\n',
         '"name": "Garden Rooms & Garden Homes in Ireland",\n'
         '      "description": "%s",\n'
         '      "inLanguage": "en-IE",\n'
         '      "dateModified": "%s",\n'
         '      "primaryImageOfPage": { "@type": "ImageObject", "url": "https://plotnua.ie/%s" },\n'
         % (LITG_DESC_LD, LITG_MODIFIED, LITG_IMG)),
        ('<main id="pn-main">\n<div class="article">\n',
         '<main id="pn-main">\n<div class="article">\n' + brief(
             'Since 27 July 2026, two different buildings can go at the end of an Irish back garden '
             'without a planning application, if the conditions are met. A <strong>garden room</strong> '
             'of up to 30&nbsp;m&sup2; &mdash; an office, studio or gym where nobody sleeps. And, new '
             'in 2026, a detached <strong>garden home</strong> of 32 to 45&nbsp;m&sup2; that somebody can '
             'live in, with two notices to file and a window that closes at the end of 2030. The '
             'Building Regulations keep their own, separate 25&nbsp;m&sup2; threshold. Below: what '
             'changed, what counts towards each limit, and how to check your own garden. Thinking of '
             'a sauna or a hot tub instead? <a href="discovery-garden-retreat.html">Garden Retreat</a> '
             'covers how the same rules read for each.')),
        ("<h2>A room and a home are not the same project.</h2>",
         "<h2>A garden room and a garden home are not the same project.</h2>"),
        ("<h2>If you want the conditions in full.</h2>",
         "<h2>The 2026 planning conditions in full.</h2>"),
    ],
    "discovery-garden-retreat.html": [
        ('<meta name="description" content="A sauna cabin, a hot tub and a cold plunge are not the same '
         'thing in Irish planning law. How the definitions read for each, what the 30 m² and 25 m² limits '
         'mean, and what the law still does not settle.">',
         '<meta name="description" content="%s">' % GR_DESC),
        ('<link rel="canonical" href="https://plotnua.ie/discovery-garden-retreat.html">\n',
         '<link rel="canonical" href="https://plotnua.ie/discovery-garden-retreat.html">\n'
         + preload(GR_IMG)),
        ('"name": "Garden Saunas, Hot Tubs & Cold Plunges in Ireland: the Planning Rules",\n'
         '      "description": "How Irish planning law reads for a sauna cabin, a freestanding hot tub, '
         'a sunken tub and a cold plunge \\u2014 and what it does not settle.",\n'
         '      "inLanguage": "en-IE",\n'
         '      "dateModified": "2026-10-14",\n',
         '"name": "Garden Saunas, Hot Tubs & Cold Plunges in Ireland",\n'
         '      "description": "Garden saunas, hot tubs and cold plunges in Ireland: real published prices, '
         'the space each needs, and how the 30 m\\u00b2 and 25 m\\u00b2 limits apply.",\n'
         '      "inLanguage": "en-IE",\n'
         '      "dateModified": "%s",\n'
         '      "primaryImageOfPage": { "@type": "ImageObject", "url": "https://plotnua.ie/%s" },\n'
         % (GR_MODIFIED, GR_IMG)),
        ('owned by atlas-tools/build-maker-explorer.py. Do not hand-edit. -->\n<div class="article">\n',
         'owned by atlas-tools/build-maker-explorer.py. Do not hand-edit. -->\n<div class="article">\n'
         + brief(
             'A garden sauna, a wood-fired hot tub and a cold plunge each ask something different of an '
             'Irish garden: space, a level base, a heater or a stove, and somewhere for the water to go. '
             'Below are published prices for one checked product of each, what each one needs, and how '
             'the planning limits read &mdash; the 30&nbsp;m&sup2; garden-structure limit, 25&nbsp;m&sup2; '
             'of open garden left behind, and the separate 25&nbsp;m&sup2; Building Regulations threshold. '
             'Thinking of a garden room or a garden home instead? '
             'The <a href="discovery-living-in-the-garden.html">Living in the Garden Discovery</a> covers those rules.')),
    ],
    "discovery-hidden-bins.html": [
        ("<title>Wheelie Bin Storage Ideas in Ireland: Hidden &amp; Underground | PlotNua</title>",
         "<title>Wheelie Bin Storage Ireland: Hidden &amp; Underground | PlotNua</title>"),
        ('<meta name="description" content="Explore ways to hide wheelie bins at an Irish home, from timber '
         'stores to underground lifts. Compare available options and planning considerations.">',
         '<meta name="description" content="%s">' % HB_DESC),
        ('<link rel="canonical" href="https://plotnua.ie/discovery-hidden-bins.html">\n',
         '<link rel="canonical" href="https://plotnua.ie/discovery-hidden-bins.html">\n'
         + preload(HB_IMG)),
        ('</head>\n',
         jsonld("discovery-hidden-bins", "Wheelie Bin Storage Ireland: Hidden & Underground",
                "Three ways to hide wheelie bins at an Irish home, from bin stores to underground lifts: "
                "what is available in Ireland, costs and the 2026 planning change.",
                "The Hidden Bins", HB_IMG) + '</head>\n'),
        ('<main id="pn-main">\n<div class="article">\n',
         '<main id="pn-main">\n<div class="article">\n' + brief(
             'There are three ways to stop wheelie bins being the first thing anyone sees at an Irish '
             'home. <strong>Hide</strong> them in a bin store, the most widely available option, from the '
             'low hundreds of euro. <strong>Integrate</strong> the storage into the frontage, made to order '
             'by several Irish makers. Or make them <strong>disappear</strong> below ground on a lift '
             '&mdash; real, installed equipment abroad, but with no Irish supplier verified for a single '
             'house. Since July 2026, Class&nbsp;62 provides an exempted route for above-ground bin '
             'storage, subject to conditions; it does not cover an underground system.')),
        ("<h2>Your three options</h2>",
         "<h2>Your three bin storage options</h2>"),
    ],
    "discovery-driveway-income.html": [
        ("<title>Renting Out Your Driveway for Parking in Ireland | PlotNua</title>",
         "<title>Rent Out Your Driveway in Ireland: Tax &amp; Planning | PlotNua</title>"),
        ('<meta name="description" content="Could your unused driveway earn money from parking? Explore '
         'location, likely demand, tax, insurance and planning questions for Irish homeowners.">',
         '<meta name="description" content="%s">' % DI_DESC),
        ('<link rel="canonical" href="https://plotnua.ie/discovery-driveway-income.html">\n',
         '<link rel="canonical" href="https://plotnua.ie/discovery-driveway-income.html">\n'
         + preload(DI_IMG)),
        ('</head>\n',
         jsonld("discovery-driveway-income", "Rent Out Your Driveway in Ireland: Tax & Planning",
                "Could your driveway earn money from parking? What Irish homeowners report, how tax and "
                "insurance apply, and what planning law does not yet settle.",
                "Driveway Income", DI_IMG) + '</head>\n'),
        ('<main class="article" id="pn-main">\n',
         '<main class="article" id="pn-main">\n' + brief(
             'An empty driveway can earn money from parking when it is near somewhere people need to '
             'reach: an airport, a hospital, a station or a town centre. Irish homeowners have reported '
             'around &euro;50 to &euro;65 a week. The income is taxable and Rent-a-Room Relief does not '
             'apply; check with your insurer before anyone parks; and no published Irish planning '
             'decision yet settles whether letting a driveway is still incidental to a home. If bins '
             'take up the space, <a href="discovery-hidden-bins.html">The Hidden Bins</a> looks at '
             'getting them out of the way.')),
        ("<h2>Is your driveway suitable?</h2>",
         "<h2>Is your driveway suitable for renting out?</h2>"),
    ],
    "index.html": [
        # The home hero is opacity:0 until its image has loaded, so an earlier
        # start on the download is an earlier reveal. No file changes.
        ('<link rel="canonical" href="https://plotnua.ie/">\n',
         '<link rel="canonical" href="https://plotnua.ie/">\n' + preload(HOME_IMG)),
    ],
    "search.html": [
        ('<meta name="robots" content="index, follow">',
         '<meta name="robots" content="noindex, follow">'),
    ],
    "sitemap.xml": [
        ('  <url><loc>https://plotnua.ie/search.html</loc><lastmod>2026-10-08</lastmod><changefreq>weekly'
         '</changefreq><priority>0.9</priority></url>\n', ''),
    ],
}

def apply_file(fname, edits):
    p = ROOT / fname
    src = p.read_text(encoding="utf-8")
    out = src
    problems = []
    for old, new in edits:
        # Phase 1b (hero WebP derivatives) supersedes the JPEG preload with a
        # WebP imagesrcset preload; that later state satisfies this edit.
        if new and 'rel="preload" as="image" href=' in new and \
                'rel="preload" as="image" type="image/webp"' in out:
            continue
        # Phase 4 (19 Oct 2026) retires the aerial hero on the homepage: its
        # LCP is the Possibility Reveal scene, preloaded as AVIF from the
        # component's own encodings. That later state satisfies this edit on
        # index.html ONLY, and only when exactly one such preload is present.
        if fname == "index.html" and new == old + preload(HOME_IMG) and \
                (out.count(PHASE4_REVEAL_PRELOAD) == 1 or out.count(H6_PRELOAD) == 1):
            continue
        if new and new in out and (old not in out or old in new):
            # already applied (for insertions old is contained in new)
            if out.count(new) == 1:
                continue
        n = out.count(old)
        if new == "" and n == 0:
            continue  # removal already applied
        if n != 1:
            problems.append("%s: anchor occurs %d times: %r" % (fname, n, old[:90]))
            continue
        out = out.replace(old, new)
    return src, out, problems


def file_date(fname):
    """The page's real last modification: today if it is being changed now
    (uncommitted), otherwise the date of the last commit that touched it."""
    import subprocess
    dirty = subprocess.run(["git", "status", "--porcelain", "--", fname], cwd=ROOT,
                           capture_output=True, text=True).stdout.strip()
    if dirty:
        return TODAY
    # A commit that changes no page CONTENT (e.g. Phase 1b's WebP <picture>
    # wrapping) carries the marker "lastmod-neutral" in its message and does
    # not move lastmod. Everything else does.
    d = subprocess.run(["git", "log", "-1", "--format=%as", "--invert-grep",
                        "--grep=lastmod-neutral", "--", fname], cwd=ROOT,
                       capture_output=True, text=True).stdout.strip()
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", d):
        die("no commit date for %s" % fname)
    return d


def sitemap_lastmod(text, pending):
    def fix(m):
        path = m.group(1) or "index.html"
        if not (ROOT / path).exists():
            die("sitemap lists %s, which is not on disk" % path)
        d = TODAY if path in pending else file_date(path)
        return "<loc>https://plotnua.ie/%s</loc>%s<lastmod>%s</lastmod>" % (m.group(1), m.group(2), d)
    out, n = re.subn(r"<loc>https://plotnua\.ie/([^<]*)</loc>(\s*)<lastmod>[^<]*</lastmod>", fix, text)
    if n != text.count("<loc>"):
        die("sitemap: %d <loc> entries but %d dated" % (text.count("<loc>"), n))
    return out


def main():
    changed, problems = {}, []
    for fname, edits in EDITS.items():
        src, out, prob = apply_file(fname, edits)
        problems += prob
        if out != src:
            changed[fname] = out
    # sitemap lastmod from evidence (git), applied on top of the edits
    sm_src = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
    sm = sitemap_lastmod(changed.get("sitemap.xml", sm_src), set(changed))
    if sm != sm_src:
        changed["sitemap.xml"] = sm
    elif "sitemap.xml" in changed and changed["sitemap.xml"] == sm_src:
        del changed["sitemap.xml"]
    if problems:
        die("\n  " + "\n  ".join(problems))
    # post-conditions
    for fname in EDITS:
        t = changed.get(fname) or (ROOT / fname).read_text(encoding="utf-8")
        if fname.endswith(".html"):
            t = re.sub(r"<!--.*?-->", " ", t, flags=re.S)
            if t.count("<title>") > 1 or t.count('name="description"') > 1:
                die("%s would carry a duplicate title/description" % fname)
    if CHECK:
        if changed:
            die("CHECK: %d file(s) not yet in the Phase 1 state: %s"
                % (len(changed), ", ".join(sorted(changed))))
        print("SEO PHASE 1 · CHECK OK — all edits present, nothing written")
        return
    for fname, out in changed.items():
        (ROOT / fname).write_text(out, encoding="utf-8")
        print("  wrote %s" % fname)
    print("SEO PHASE 1 · applied (%d file(s) changed)" % len(changed))


if __name__ == "__main__":
    main()
