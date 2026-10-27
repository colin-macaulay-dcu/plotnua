#!/usr/bin/env python3
"""DISC-032 · The Supper Club at Home: page, SEO, isolation and wording proof (read-only).

    python3 atlas-tools/prove-disc032-page.py            # release candidate: noindex, unlinked
    python3 atlas-tools/prove-disc032-page.py --launch   # after the separately approved launch
    python3 atlas-tools/prove-disc032-page.py --prove    # capability: planted faults must all be caught

Checks the page and the founder's limits (Stage 2 refinements A-E; Phase 1 and Phase 2 decisions,
27 Oct 2026):
  S1  one <title>, meta description, canonical, Open Graph / Twitter image; robots noindex, follow
      (release candidate) or index, follow (--launch)
  S2  JSON-LD parses; no Product, Offer, price, Event, LocalBusiness, FAQPage, Review or rating data
  S3  exactly one H1, and it carries the hero question
  S4  every local href/src/srcset on the page resolves to a file
  S5  the hero is the shared pn-compare component: 35% start, both approved images, keyboard range
      with label and description, compact mobile title (aria-hidden), the mobile instruction
  S6  the AI-generated illustration label, and the fictional-home statement
  S7  ISOLATION. Release candidate: NOT in sitemap.xml, the Discovery Library or the search index,
      and no other page links to it. --launch: in all three
  S8  no form, no booking, registration, payment or matching mechanism; no euro or sterling figure;
      none of the prohibited phrases (exemptions, partners, earnings, matching)
  S9  the cautions the founder required are present verbatim
  S10 no real supper club is named before its permission is recorded
  S11 the three models, the homeowner-chef partnership (model 2) first and primary
Prints "DISC-032 PAGE · OK" only when every check passes.
"""
import html, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = "discovery-supper-club-at-home.html"
URL = "https://plotnua.ie/" + PAGE
LAUNCH = "--launch" in sys.argv
QUESTION = "What if your home could become someone else’s favourite restaurant?"
PROHIBITED = ("exempt from", "no permission needed", "doesn’t need planning", "does not need planning",
              "our partner", "plotnua partner", "verified partner", "official partner", "you could earn",
              "earn up to", "guaranteed", "matching service", "we match", "we’ll introduce", "we will introduce",
              "book a chef", "book now", "buy your tickets", "sign up now", "register now", "licensed to sell",
              "no licence needed", "byob is fine", "fully insured")
REQUIRED = (
    "Being occasional or small doesn’t automatically put it outside the rules.",
    "Leaving drinks out of the ticket price doesn’t settle every licensing question",
    "We haven’t yet found a verified example of a chef running ticketed dinners in someone else’s home in Ireland, so treat this as a possibility, not a proven model.",
    "PlotNua doesn’t arrange supper clubs or introduce chefs to homeowners.",
    "PlotNua doesn’t publish earnings estimates for home supper clubs.",
    "There’s no standard rate, and we won’t pretend there is.",
    "This page is general information, not legal, tax or insurance advice.",
    "Nothing is set up yet: we don’t arrange introductions, take bookings or sell tickets.",
)
NAMED = ("Landlover", "Bear in Mind", "Edergole", "Aideen", "Sheena", "O’Byrne", "O'Byrne", "Whitestown")


def read(p):
    return open(os.path.join(ROOT, p), encoding="utf-8").read()


def visible(s):
    t = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", " ", s, flags=re.S)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", t)))


def check(s, sitemap, library, index, others):
    P = []
    need = lambda c, m: None if c else P.append(m)
    # S1
    need(len(re.findall(r"<title>[^<]+</title>", s)) == 1, "S1 one <title>")
    robots = "index, follow" if LAUNCH else "noindex, follow"
    for pat in (r'<meta name="description" content="[^"]{60,}"', r'<link rel="canonical" href="%s"' % re.escape(URL),
                r'<meta property="og:url" content="%s"' % re.escape(URL),
                r'<meta property="og:image" content="https://plotnua\.ie/assets/disc032/img/DISC-032-og-1200x630\.jpg"',
                r'<meta name="twitter:card" content="summary_large_image"', r'<meta name="robots" content="%s">' % robots):
        need(re.search(pat, s), "S1 missing: " + pat)
    need(len(re.findall(r'<meta name="robots"', s)) == 1, "S1 exactly one robots meta")
    # S2
    blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', s, re.S)
    need(blocks, "S2 no JSON-LD")
    for b in blocks:
        try:
            j = json.dumps(json.loads(b))
        except ValueError as e:
            P.append("S2 JSON-LD does not parse: %s" % e); continue
        for bad in ('"Product"', '"Offer"', '"price"', '"priceCurrency"', '"AggregateOffer"', '"LocalBusiness"',
                    '"Event"', '"FoodEvent"', '"FAQPage"', '"Review"', '"AggregateRating"', '"Restaurant"'):
            need(bad not in j, "S2 unsupported structured data: " + bad)
    # S3
    h1 = re.findall(r"<h1[\s>].*?</h1>", s, re.S)
    need(len(h1) == 1, "S3 exactly one H1")
    need(h1 and QUESTION in visible(h1[0]), "S3 the H1 carries the hero question")
    # S4
    refs = set(re.findall(r'(?:href|src)="([^"#?]+)', s)) | {
        u.strip().split(" ")[0] for ss in re.findall(r'srcset="([^"]+)"', s) for u in ss.split(",")}
    for ref in refs:
        if ref.startswith(("http:", "https:", "mailto:", "tel:", "data:")) or not ref:
            continue
        need(os.path.exists(os.path.join(ROOT, ref.lstrip("/"))), "S4 missing local file: " + ref)
    # S5
    fig = re.search(r'<figure class="pn-compare pn-compare--hero"[^>]*>.*?</figure>', s, re.S)
    need(fig, "S5 no pn-compare hero")
    if fig:
        f = fig.group(0)
        need('data-start="35"' in f, "S5 not a 35% start")
        need("DISC-032-before-1536.jpg" in f and "DISC-032-possible-1536.jpg" in f, "S5 the approved pair is not both in the hero")
        need(f.index("pn-compare__possible") < f.index("pn-compare__before"), "S5 layer order")
        need(re.search(r'<input class="pn-compare__range" type="range"[^>]*aria-describedby="(\w+)"[^>]*aria-label="[^"]{20,}"', f), "S5 keyboard range label/description")
        m = re.search(r'aria-describedby="(\w+)"', f)
        need(m and ('id="%s"' % m.group(1)) in f, "S5 the range description target is missing")
        need("Slide to discover what’s possible." in visible(f), "S5 the mobile instruction")
    need('<div class="sc-mob-title" aria-hidden="true">' in s, "S5 the compact mobile title (aria-hidden)")
    need('href="assets/identity/pn-compare.css"' in s and 'src="assets/identity/pn-compare.js"' in s, "S5 component not linked")
    # S6
    v = visible(s)
    need(v.count("AI-generated illustration") >= 1, "S6 no AI-generated illustration label")
    need("AI-generated illustrations of a fictional home" in v, "S6 the fictional-home statement")
    # S7
    listed = (("<loc>%s</loc>" % URL) in sitemap, ('href="%s"' % PAGE) in library, ('"%s"' % PAGE) in index)
    if LAUNCH:
        need(all(listed), "S7 launch: sitemap / Library card / search index missing")
    else:
        need(not any(listed), "S7 ISOLATION: the release candidate is listed (sitemap, Library or search index)")
        need(not others, "S7 ISOLATION: linked from %s" % ", ".join(sorted(others))[:200])
    # S8
    need("<form" not in s.lower(), "S8 a form")
    need(len(re.findall(r"<input\b", s)) == 2, "S8 inputs other than the search field and the comparison range")
    body = s[:s.find("<footer")]          # the shared footer's contact address is site-wide, not this page's
    need("mailto:" not in body and "tel:" not in body, "S8 a contact or booking mechanism in the page body")
    need(not re.search(r"[€£]\s?\d|\d\s?(euro|EUR)\b", v), "S8 a euro or sterling figure appears")
    low = v.lower()
    for bad in PROHIBITED:
        need(bad.lower() not in low, "S8 prohibited phrase: " + bad)
    # S9
    for claim in REQUIRED:
        need(claim in v, "S9 required caution missing: " + claim[:60])
    need(v.count("Registration isn’t open yet.") == 2, "S9 registration closed, both cards")
    need(len(re.findall(r"Still being confirmed|Open question", v)) >= 6, "S9 the six provisional notes")
    # S10
    for n in NAMED:
        need(n not in v, "S10 a real supper club or person named without recorded permission: " + n)
    # S11
    for i in ("scWay1", "scWay2", "scWay3"):
        need(('id="%s"' % i) in s, "S11 model card " + i)
    need(s.find('id="scWay2"') < s.find('id="scWay1"') and 'is-primary pd-s-7" aria-labelledby="scWay2"' in s,
         "S11 model 2 (the homeowner-chef partnership) is not first and primary")
    return P


def inputs():
    s = read(PAGE)
    others = set()
    for dp, dn, fn in os.walk(ROOT):
        if any(x in dp for x in ("/.git", "/node_modules", "/atlas-tools", "/governance", "/.github")):
            continue
        for f in fn:
            if f.endswith(".html") and f != PAGE:
                t = open(os.path.join(dp, f), encoding="utf-8", errors="replace").read()
                t = re.sub(r"<!--.*?-->", " ", t, flags=re.S)
                if re.search(r'href="(?:/|\.\./)?%s' % re.escape(PAGE), t):
                    others.add(os.path.relpath(os.path.join(dp, f), ROOT))
    return s, read("sitemap.xml"), read("discoveries.html"), read("search-index-v1.json"), others


def prove():
    s, sm, lib, idx, others = inputs()
    faults = [
        ("robots flipped to index", lambda a: (a[0].replace('content="noindex, follow"', 'content="index, follow"'),) + a[1:]),
        ("sitemap entry", lambda a: (a[0], a[1] + "<loc>%s</loc>" % URL) + a[2:]),
        ("Library card", lambda a: (a[0], a[1], a[2] + '<a href="%s">' % PAGE) + a[3:]),
        ("search index", lambda a: a[:3] + (a[3] + '"%s"' % PAGE, a[4])),
        ("linked from a live page", lambda a: a[:4] + ({"discovery-a-home-for-art.html"},)),
        ("a mailto booking link", lambda a: (a[0].replace("</main>", '<a href="mailto:x@y.ie">Book</a></main>'),) + a[1:]),
        ("a form", lambda a: (a[0].replace("</main>", "<form></form></main>"),) + a[1:]),
        ("an earnings figure", lambda a: (a[0].replace("</main>", "<p>Hosts make €400 a night.</p></main>"),) + a[1:]),
        ("an exemption claim", lambda a: (a[0].replace("</main>", "<p>Occasional dinners are exempt from planning.</p></main>"),) + a[1:]),
        ("a partner claim", lambda a: (a[0].replace("</main>", "<p>Our partner chefs.</p></main>"),) + a[1:]),
        ("a named supper club", lambda a: (a[0].replace("</main>", "<p>Landlover</p></main>"),) + a[1:]),
        ("licensing caution removed", lambda a: (a[0].replace("doesn&rsquo;t settle every licensing question", "settles it"),) + a[1:]),
        ("Model 2 caution removed", lambda a: (a[0].replace("We haven&rsquo;t yet found a verified example", "We found an example"),) + a[1:]),
        ("second H1", lambda a: (a[0].replace("</main>", "<h1>x</h1></main>"),) + a[1:]),
        ("Event structured data", lambda a: (a[0].replace('"@type": "WebPage"', '"@type": "Event"'),) + a[1:]),
        ("40% start", lambda a: (a[0].replace('data-start="35"', 'data-start="40"'),) + a[1:]),
        ("mobile title read aloud", lambda a: (a[0].replace('<div class="sc-mob-title" aria-hidden="true">', '<div class="sc-mob-title">'),) + a[1:]),
        ("AI label removed", lambda a: (a[0].replace("AI-generated illustration", "Illustration"),) + a[1:]),
        ("registration opened", lambda a: (a[0].replace("Registration isn&rsquo;t open yet.", "Register below.", 1),) + a[1:]),
    ]
    clean = check(s, sm, lib, idx, others)
    if clean:
        print("DISC-032 PAGE PROOF · the clean page fails: %s" % clean[0]); sys.exit(1)
    missed = []
    for name, f in faults:
        if not check(*f((s, sm, lib, idx, others))):
            missed.append(name)
    if missed:
        print("DISC-032 PAGE PROOF · NOT CAUGHT: " + ", ".join(missed)); sys.exit(1)
    print("DISC-032 PAGE PROOF · OK · %d planted faults, 0 not caught" % len(faults))


if __name__ == "__main__":
    if "--prove" in sys.argv:
        prove(); sys.exit(0)
    problems = check(*inputs())
    if problems:
        print("DISC-032 PAGE · FAILED")
        for p in problems:
            print("  " + p)
        sys.exit(1)
    print("DISC-032 PAGE · OK (S1-S11) · %s" % ("launched: listed and indexable" if LAUNCH else "release candidate: noindex, unlisted, unlinked"))
