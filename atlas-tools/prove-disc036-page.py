#!/usr/bin/env python3
"""DISC-036 · Extend the House: page, SEO, claims, privacy and integration proof (read-only).
PLOTNUA-BUILD-001 Stage 1 (founder development authorisation, private preview only, 5 Nov 2026); final hero
integration (founder authorisation, private preview only, 5 Nov 2026).

    python3 atlas-tools/prove-disc036-page.py [--self-test]

  E1  one <title> (the approved search identity), meta description, canonical, index/follow
  E2  JSON-LD parses; no Product, Offer, price, LocalBusiness, Review or FAQPage data
  E3  exactly one H1 ("Extend the House"), the hero question and the search-identity line
  E4  every local href/src/srcset on the page resolves to a file
  E5  the hero is the shared pn-compare component, opening on 100 % BEFORE, keyboard-operable, with labels;
      its two layers are the founder's image pair (DISC-036-POSSIBLE / -BEFORE, WebP sources with a JPEG
      fallback, 1671 x 941, a 4:5 phone crop), each with a descriptive alt, and the hero carries the registered
      AI label (PROPERTY) in the figure and under the hero; the retired drawing label is gone
  E6  six chapters in order with their titles; the six types in chapter 02; the four routes in chapter 06,
      each answering the same five questions (parity)
  E7  chapter 03: 27 July 2026, Class 1, 45 m2 (was 40), rear only, 1 October 1964, the upstairs limits
      (12 / 20 m2), 2 m, 8 m (was 11), 25 m2, protected structure, ACA, Section 5 (EUR 80), building
      regulations always apply, the 45 m2 Commencement Notice threshold, project supervisors, not legal advice;
      no blanket exemption wording
  E8  chapter 04: the roles, protected titles stated only for architect / quantity surveyor / building surveyor,
      register links (RIAI, SCSI, Engineers Ireland, HSA), "Not every project needs everyone", no firm named
  E9  chapter 05: the eleven budget components; no cost per square metre, no estimate, no calculator:
      the only euro figure on the page is the Section 5 fee
  E10 chapter 06: links to Living in the Garden, The Outdoor Room and Stay in the House You Love, all live
      files; attic and garage say plainly that no Discovery exists yet (no speculative links)
  E11 the brief: nine questions; no <form>, no fetch / XHR / beacon / endpoint / Formspree / Workers; the
      save goes only through the frozen journey-save block (byte-identical to the Hidden Cars copy); the
      free-text note is never put in the saved payload; print and My Plot controls present
  E12 analytics: exactly the three named events, with only fixed parameters (journey / destination); no
      answer value, note or brief text is read into an event
  E13 no partner, supplier, commission, referral, discount or paid-service wording; no "increase the value"
      claim; the value caveat is present
  E14 sitemap entry and search-index entry; the four governed search entries target this page; exactly one
      Library card, in Space, showing the POSSIBLE (never the BEFORE) with the AI chip
  E15 the drawings in the page equal what build-disc036-drawings.py builds (--check)
  E16 provenance: every DISC-036 image the page and its card use is a recorded derivative of a declared
      AI_ILLUSTRATION master that permits that surface; the share image is the POSSIBLE; the web copies equal
      what build-disc036-images.py builds (--check)
Prints "DISC-036 PAGE · OK" only when every check passes.
"""
import html, json, os, re, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = "discovery-extend-the-house.html"
URL = "https://plotnua.ie/" + PAGE
DRAW_LABEL = "Illustrative drawing by PlotNua. Not a design for any home."   # retired with the interim drawn hero
AI_LABEL = "Illustrative AI-generated visualisation. Not an actual property."   # build-ai-disclosure-below.py PROPERTY


def text(fragment):
    t = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", " ", fragment, flags=re.S)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", t)))


def read(p):
    return open(os.path.join(ROOT, p), encoding="utf-8").read()


def check(s, files):
    problems = []

    def need(cond, msg):
        if not cond:
            problems.append(msg)

    flat = text(s)
    low = flat.lower()
    scripts = "\n".join(re.findall(r"<script(?:\s[^>]*)?>(.*?)</script>", s, re.S))

    # E1
    need(len(re.findall(r"<title>[^<]+</title>", s)) == 1, "E1 one <title>")
    need("<title>House Extensions in Ireland: Planning, Costs and Where to Start | PlotNua</title>" in s, "E1 the approved search identity")
    for pat in (r'<meta name="description" content="[^"]{60,160}"', r'<link rel="canonical" href="%s"' % re.escape(URL),
                r'<meta property="og:url" content="%s"' % re.escape(URL), r'<meta name="robots" content="index, follow"'):
        need(re.search(pat, s), "E1 missing: " + pat)

    # E2
    blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', s, re.S)
    need(blocks, "E2 no JSON-LD")
    for b in blocks:
        try:
            j = json.dumps(json.loads(b))
        except ValueError as e:
            problems.append("E2 JSON-LD does not parse: %s" % e); continue
        for bad in ('"Product"', '"Offer"', '"price"', '"LocalBusiness"', '"Review"', '"FAQPage"', '"AggregateOffer"'):
            need(bad not in j, "E2 unsupported structured data: " + bad)

    # E3
    need(len(re.findall(r"<h1[\s>]", s)) == 1, "E3 exactly one H1")
    need("<h1>Extend the House</h1>" in s, "E3 the H1 is the working title")
    need("What if your home could grow into the space it&rsquo;s been missing?" in s, "E3 the hero question")
    need("House extensions in Ireland: planning, costs and where to start." in s, "E3 the search-identity line")

    # E4
    refs = set(re.findall(r'(?:href|src)="([^"#?]+)', s)) | {
        u.strip().split(" ")[0] for ss in re.findall(r'(?:srcset|imagesrcset)="([^"]+)"', s) for u in ss.split(",")}
    for ref in refs:
        if ref.startswith(("http:", "https:", "mailto:", "tel:", "data:", "/")) or not ref:
            continue
        need(files(ref), "E4 missing local file: " + ref)

    # E5
    fig = re.search(r'<figure class="pn-compare pn-compare--hero"[^>]*>.*?</figure>', s, re.S)
    need(fig, "E5 no pn-compare hero")
    if fig:
        f = fig.group(0)
        need('data-start="100"' in f and 'value="100"' in f, "E5 the hero must open on 100% BEFORE")
        need(f.index("pn-compare__possible") < f.index("pn-compare__before"), "E5 BEFORE must be the overlay layer")
        need('>Before</p>' in f and '>Possible</p>' in f, "E5 Before / Possible labels")
        need('class="pn-compare__range"' in f and "aria-label=" in f and "arrow keys" in f, "E5 keyboard/screen-reader control")
        for role in ("POSSIBLE", "BEFORE"):
            need(f.count("assets/disc036/img/DISC-036-%s-" % role) == 6, "E5 the %s layer's six sources (4 WebP widths, phone WebP, JPEG)" % role)
        need(f.count('width="1671" height="941"') == 2 and "<svg" not in f, "E5 the two layers are the founder's 1671 x 941 images")
        need(len(re.findall(r'<img [^>]*alt="(?:Possible|Before): [^"]{60,}"', f)) == 2, "E5 each layer carries a descriptive alt")
        need(re.search(r'<img fetchpriority="high" src="assets/disc036/img/DISC-036-BEFORE-1024.jpg"', f), "E5 the BEFORE (seen first) loads first")
        need(AI_LABEL in f, "E5 the in-figure AI label")
    need(s.count(AI_LABEL) == 2, "E5 the AI label in the figure and under the hero")
    need(DRAW_LABEL not in s, "E5 the retired drawing label is gone")
    need("pn-compare.js" in s and "pn-compare.css" in s, "E5 the shared component's files")
    need(s.count("https://plotnua.ie/assets/disc036/img/DISC-036-og-1200x630.jpg") == 2 and 'name="twitter:card" content="summary_large_image"' in s,
         "E16 the share image (og:image, twitter:image) is the POSSIBLE share crop")

    # E6
    order = re.findall(r'id="lg-ch0(\d)"', s)
    need(order == ["1", "2", "3", "4", "5", "6"], "E6 six chapters in order (found %s)" % order)
    for t in ("What an extension can change.", "Six shapes an extension can take.", "What the rules say, and what they leave to you.",
              "Not every project needs everyone.", "What makes up the total.", "Where else could the room come from?"):
        need(t in flat, "E6 chapter title missing: " + t)
    types = re.findall(r'<h3 id="ehT\dH">([^<]+)</h3>', s)
    need(types == ["Rear extension", "Side extension", "Side-return extension", "Kitchen extension", "Wrap-around extension",
                   "Two-storey extension"], "E6 the six types in order: %s" % types)
    routes = re.findall(r'<li class="or-way" aria-labelledby="ehR(\d)H">(.*?)</li>', s, re.S)
    need([r[0] for r in routes] == ["1", "2", "3", "4"], "E6 four routes")
    rows = [tuple(re.findall(r"<dt>([^<]+)</dt>", r[1])) for r in routes]
    need(len(set(rows)) == 1 and rows and rows[0] == ("What you gain", "What it uses", "During the work", "Planning start", "Ask"),
         "E6 parity: every route answers the same five questions (%s)" % rows)
    lens = [len(text(r[1])) for r in routes]
    need(lens and max(lens) <= 1.35 * min(lens), "E6 parity: the routes are of comparable length %s" % lens)

    # E7
    pl = re.search(r'<section class="pd-section pd-gapL" id="planning".*?</section>', s, re.S)
    need(pl, "E7 chapter 03 section")
    if pl:
        p = text(pl.group(0))
        for t in ("27 July 2026", "Class 1", "45 m", "was 40 m", "to the rear", "1 October 1964", "12 m", "20 m", "2 metres",
                  "8 m", "was 11 m", "25 m", "protected structure", "Architectural Conservation Area", "apartments", "Section 5",
                  "€80", "four weeks", "Building Regulations", "Commencement Notice", "14 to 28 days", "assigned certifier",
                  "opt-out", "project supervisors", "30 days", "not legal advice", "can’t tell you whether"):
            need(t in p, "E7 planning point missing: " + t)
    for bad in ("no planning permission is needed", "never needs planning", "always exempt", "don’t need planning permission",
                "do not need planning permission", "doesn’t need planning permission.", "guaranteed exempt", "is exempt from planning permission."):
        need(bad not in low, "E7 blanket exemption wording: " + bad)

    # E8
    who = re.search(r'<section class="pd-section" id="who-does-what".*?</section>', s, re.S)
    need(who, "E8 chapter 04 section")
    if who:
        w = who.group(0)
        ul = re.search(r'<ul class="eh-roles.*?</ul>', w, re.S)
        names = re.findall(r"<li><h3>([^<]+)</h3>", ul.group(0) if ul else "")
        need(names == ["Architect", "Architectural technologist", "Structural engineer", "Quantity surveyor", "Building surveyor",
                       "Builder", "Assigned certifier", "Project supervisors"], "E8 the roles: %s" % names)
        prot = re.findall(r'<li><h3>([^<]+)</h3><span class="eh-title is-protected">Protected title</span>', w)
        need(prot == ["Architect", "Quantity surveyor", "Building surveyor"], "E8 protected titles only where the 2007 Act protects them: %s" % prot)
        for u in ("riai.ie", "scsi.ie/check", "engineersireland.ie", "hsa.ie"):
            need(u in w, "E8 register or guidance link missing: " + u)
        need("doesn’t recommend or list individual firms" in text(w), "E8 the no-firms statement")
        need("Not every project needs everyone." in flat, "E8 the not-every-project framing")

    # E9
    co = re.search(r'<section class="pd-section" id="cost".*?</section>', s, re.S)
    need(co, "E9 chapter 05 section")
    if co:
        ks = re.findall(r'<span class="eh-cost-k">([^<]+)</span>', co.group(0))
        need([html.unescape(k) for k in ks] == ["Design and professional fees", "Surveys and investigations", "Planning-related costs",
              "Construction", "Structural work", "Glazing", "Kitchen and interior fit-out", "Mechanical and electrical",
              "External works", "VAT", "Contingency"], "E9 the eleven components: %s" % ks)
    euros = sorted({e.rstrip(",.") for e in re.findall(r"€\s?\d[\d,]*(?:\.\d\d)?", flat)})
    need(euros == ["€80"], "E9 the only euro figure is the Section 5 fee: %s" % euros)
    need(not re.search(r"£\s?\d", flat), "E9 a sterling figure")
    need(not re.search(r"(?:€|eur)\s?/?\s?m(?:2|²)|per square met(?:re|er)\s*(?:of|is|costs|from)", low), "E9 a cost per square metre")
    for bad in ("calculator", "estimate your", "typical cost", "average cost", "costs around", "costs about"):
        need(bad not in low.replace("no cost per square metre or estimate", ""), "E9 cost-estimate wording: " + bad)

    # E10
    ch6 = s[s.index('id="lg-ch06"'):] if 'id="lg-ch06"' in s else ""
    for link in ("discovery-living-in-the-garden.html", "discovery-the-outdoor-room.html", "discovery-stay-in-the-house-you-love.html"):
        need(('href="%s"' % link) in ch6 and files(link), "E10 related link missing or not live: " + link)
    need(ch6.count("hasn’t published a Discovery on") == 2 or ch6.count("hasn&rsquo;t published a Discovery on") == 2,
         "E10 attic and garage: no Discovery yet, stated plainly")
    for spec in ("discovery-attic", "discovery-garage", "discovery-convert", "discovery-room-to-grow", "discovery-an-extra-room"):
        need(spec not in s, "E10 a speculative or retired link: " + spec)

    # E11
    bf = re.search(r'<section class="pd-section" id="extension-brief".*?</section>', s, re.S)
    need(bf, "E11 the brief section")
    if bf:
        b = bf.group(0)
        need(len(re.findall(r'<fieldset class="eh-q"', b)) == 9, "E11 nine questions")
        need('id="ehPrint"' in b and 'id="ehSaveBtn"' in b and 'href="your-plot.html?myplot=1"' in b, "E11 print and My Plot controls")
    frozen = re.search(r"<script>\n/\* PLOTNUA-JOURNEY-SAVE-BEGIN \*/.*?/\* PLOTNUA-JOURNEY-SAVE-END \*/\n</script>", s, re.S)
    own = s.replace(frozen.group(0), "") if frozen else s
    lows = re.sub(r"/\*.*?\*/|<!--.*?-->", " ", own, flags=re.S).lower()   # code and markup, not comments
    for bad in ("<form", "formspree", "workers.dev", "airtable", "xmlhttprequest", "sendbeacon", "fetch(", "navigator.sendbeacon",
                "stripe", "paypal", "checkout", 'type="email"', 'type="tel"', "eircode"):
        need(bad not in lows, "E11 data collection or payment: " + bad)
    blk = re.search(r"<script>\n/\* PLOTNUA-JOURNEY-SAVE-BEGIN \*/.*?/\* PLOTNUA-JOURNEY-SAVE-END \*/\n</script>", s, re.S)
    ref = re.search(r"<script>\n/\* PLOTNUA-JOURNEY-SAVE-BEGIN \*/.*?/\* PLOTNUA-JOURNEY-SAVE-END \*/\n</script>", read("disc022-hidden-cars-check.html"), re.S)
    need(blk and ref and blk.group(0) == ref.group(0), "E11 the journey-save block is byte-identical to the frozen copy")
    need("localstorage" not in lows and "sessionstorage" not in lows,
         "E11 no storage outside the frozen block")
    pay = re.search(r"function payload\(\) \{.*?\n  \}", s, re.S)
    need(pay and "note" not in pay.group(0) and "ehNote" not in pay.group(0), "E11 the free-text note is never saved")
    need("journeyId: JOURNEY" in s and "var JOURNEY = 'disc036-extension-brief';" in s, "E11 the journey id")

    # E12
    ev = re.findall(r"gtag\('event', ([^,]+),", s)
    names = set(re.findall(r"track\('([a-z_]+)'", s))
    need(names == {"extension_brief_open", "extension_brief_print", "extension_route_click"}, "E12 the three events: %s" % names)
    need(ev == ["name"], "E12 one gtag call, through track(): %s" % ev)
    for m in re.findall(r"track\('[a-z_]+', (\{[^}]*\})", s):
        keys = re.findall(r"(\w+):", m)
        need(set(keys) <= {"journey", "destination"}, "E12 event parameters beyond journey/destination: %s" % m)
        need("value" not in m and "read(" not in m and "note" not in m, "E12 an answer in an event: %s" % m)

    # E13
    low13 = low.replace("commission for regulation of utilities", "")
    for bad in ("partner", "commission", "referral", "discount", "sponsored", "featured supplier", "our builders", "recommended builder",
                "approved builder", "book a consultation", "paid service", "increase the value", "adds value", "add value to your home"):
        need(bad not in low13, "E13 commercial or value wording: " + bad)
    need("isn’t guaranteed to add what it costs to what your home is worth" in flat, "E13 the value caveat")

    return problems


def main():
    s = read(PAGE)
    files = lambda p: os.path.exists(os.path.join(ROOT, p))
    problems = check(s, files)

    def need(cond, msg):
        if not cond:
            problems.append(msg)

    # E14
    need(("<loc>%s</loc>" % URL) in read("sitemap.xml"), "E14 sitemap entry")
    idx = read("search-index-v1.json")
    need('"route": "%s"' % PAGE in idx or ('"%s"' % PAGE) in idx, "E14 search-index entry")
    tm = json.loads(read("atlas-tools/search-topic-map.json"))
    ph = sorted(e["phrase"] for e in tm["entries"] if PAGE in e.get("targets", []))
    need(ph == ["extension planning permission", "kitchen extension", "rear extension", "side extension"], "E14 governed search entries: %s" % ph)
    lib = read("discoveries.html")
    cards = re.findall(r'<a class="lib-card" href="%s" data-cat="([^"]+)">(.*?)</a>' % re.escape(PAGE), lib, re.S)
    need(len(cards) == 1, "E14 exactly one Library card")
    if cards:
        cat, body = cards[0]
        need(cat == "Space" and '<span class="lib-cat">Space</span>' in body, "E14 the card is in Space")
        need("DISC-036-POSSIBLE-1024.jpg" in body and "DISC-036-02-POSSIBLE-MASTER-480w.webp" in body and "BEFORE" not in body,
             "E14 the card shows the POSSIBLE, never the BEFORE")
        need('<span class="lib-aichip">AI-generated illustration</span>' in body, "E14 the card carries the AI chip")

    # E16
    reg = json.loads(read("image-provenance-records.json"))
    masters = {r["asset"]: r for r in reg["records"]}
    derivs = {d["asset"]: d for d in reg["derivatives"]}
    used = set(re.findall(r'assets/(?:disc036/img|library/img)/DISC-036-[A-Za-z0-9-]+\.(?:webp|jpg)', s))
    used |= set(re.findall(r'assets/(?:disc036/img|library/img)/DISC-036-[A-Za-z0-9-]+\.(?:webp|jpg)', "".join(b for _c, b in cards)))
    need(len(used) >= 15, "E16 the DISC-036 images in use (%d)" % len(used))
    for a in sorted(used):
        d = derivs.get(a)
        m = masters.get((d or {}).get("derived_from", {}).get("asset"))
        need(d and m and m.get("class") == "AI_ILLUSTRATION", "E16 %s is not a recorded derivative of a declared AI master" % a)
        if d and m:
            surf = "library-card" if "/library/" in a else "discovery"
            need(surf in m.get("permitted_surfaces", []), "E16 %s: its master does not permit %s" % (a, surf))
            need(not (surf == "library-card" and "BEFORE" in m["asset"]), "E16 the Library never shows the BEFORE")
    need("POSSIBLE" in derivs.get("assets/disc036/img/DISC-036-og-1200x630.jpg", {}).get("derived_from", {}).get("asset", ""),
         "E16 the share image is made from the POSSIBLE")
    r = subprocess.run([sys.executable, os.path.join(ROOT, "atlas-tools", "build-disc036-images.py"), "--check"], capture_output=True, text=True)
    need(r.returncode == 0, "E16 the web copies are not what build-disc036-images.py builds")

    # E15
    r = subprocess.run([sys.executable, os.path.join(ROOT, "atlas-tools", "build-disc036-drawings.py"), "--check"], capture_output=True, text=True)
    need(r.returncode == 0, "E15 the drawings are not built from build-disc036-drawings.py")

    if "--self-test" in sys.argv:
        faults = {
            "E3": s.replace("<h1>Extend the House</h1>", "<h1>Extend the House</h1><h1>x</h1>"),
            "E5": s.replace('data-start="100"', 'data-start="35"', 1),
            "E5 ": s.replace(AI_LABEL, "Not an actual home.", 1),
            "E16": s.replace('content="https://plotnua.ie/assets/disc036/img/DISC-036-og-1200x630.jpg"', 'content="https://plotnua.ie/assets/disc036/img/DISC-036-BEFORE-1024.jpg"', 1),
            "E6": s.replace("<dt>Ask</dt>", "<dt>Best for</dt>", 1),
            "E7": s.replace("27 July 2026", "July"),
            "E9": s.replace("contingency.</p>", "contingency.</p><p>From €2,500 per m2.</p>", 1).replace("What makes up the total.", "What makes up the total. €2,500"),
            "E11": s.replace("</main>", "<form action='https://x.workers.dev'></form></main>"),
            "E12": s.replace("track('extension_brief_print', { journey: JOURNEY }", "track('extension_brief_print', { journey: JOURNEY, answer: read() }"),
            "E13": s.replace("Six shapes an extension can take.", "Six shapes an extension can take. Ask our partner."),
            "E10": s.replace('href="discovery-the-outdoor-room.html" data-eh-route="the-outdoor-room">The Outdoor Room', 'href="discovery-attic-conversion.html">The Outdoor Room'),
        }
        missed = [k for k, t in faults.items() if not any(p.startswith(k) for p in check(t, files))]
        print("DISC-036 PAGE · SELF-TEST " + ("OK (%d planted faults caught)" % len(faults) if not missed else "MISSED %s" % missed))
        if missed:
            sys.exit(1)

    if problems:
        print("DISC-036 PAGE · FAILED")
        for p in problems:
            print("  " + p)
        sys.exit(1)
    print("DISC-036 PAGE · OK (E1-E16)")


if __name__ == "__main__":
    main()
