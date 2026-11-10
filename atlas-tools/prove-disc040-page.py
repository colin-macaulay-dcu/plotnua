#!/usr/bin/env python3
"""DISC-040 · The Home You Build: page, claims, containment and provenance proof (read-only).
Release candidate (Stage 3, prepared 10 Nov 2026), branch release-prep/disc040-the-home-you-build, NOT deployed.
Modelled on prove-disc038-page.py.

    python3 atlas-tools/prove-disc040-page.py [--self-test]

  S1  one <title>, a meta description (60-160 chars), canonical and og:url; robots "index, follow"; no preview marker left;
      datePublished and dateModified present
  S2  JSON-LD parses; no Product, Offer, price, LocalBusiness, Review, FAQPage or AggregateOffer data
  S3  exactly one H1 ("The Home You Build") and the approved hero question; no compact title above the image
  S4  every local href/src/srcset resolves to a file
  S5  the standard pn-compare hero opening at 100% BEFORE on the founder's C2PA pair (hero and phone copies), descriptive
      disclosing alts, BEFORE the priority image, tags, keyboard help, jump group, the approved AI disclosure in the figure
      and directly beneath the hero; the share image is the POSSIBLE
  S6  six chapters, in order, with the six approved kickers
  S7  the wall-section diagram is kept, labelled simplified and not to scale
  S8  maker qualifications: no confirmed commercial relationship, availability to be established with each supplier, not a
      recommendation, "none found" is not proof, PlotNua not an agent/distributor/builder; no partner or endorsement wording
  S9  regulatory cautions: the rural statement is a draft (2005 guidelines apply), the opt-out and the lender's certificate of
      compliance, general information not advice; no blanket exemption wording
  S10 figures qualified: the SCSI rebuild figures are insurance minimums, not self-build quotes; no average; speed figures are
      the makers' claims, not verified; ranges only when the evidence meets the pricing rules
  S11 no form or form control; free for homeowners, not taking orders; no fetch, XHR, beacon, Workers, Formspree, Airtable or
      WhatsApp enquiry link outside the generated header
  S13 release wiring: exactly one sitemap entry; a Search possibility record; exactly one Space Library card showing the recorded
      POSSIBLE copy with the AI chip; no governed search-map entry; the inbound link from Extend the House
  S14 provenance: every DISC-040 image in use is exactly a recorded derivative (sha256) of a declared, unchanged
      AI_ILLUSTRATION master that permits the discovery surface (the Library card's master also permits library-card)
Prints "DISC-040 PAGE · OK" only when every check passes.
"""
import hashlib, html, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = "discovery-the-home-you-build.html"
URL = "https://plotnua.ie/" + PAGE
AI = "Illustrative AI-generated visualisation. Not an actual installation."
QUESTION = "What if your new home could be made in a factory and raised on your site in weeks?"
CHAPTERS = ["The Irish self-build", "How a house is made", "Made elsewhere, built here", "From field to front door",
            "What it costs", "Make it happen"]


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

    flat = text(s); low = flat.lower()
    nocom = re.sub(r"<!--.*?-->", " ", s, flags=re.S)
    # S1
    need(len(re.findall(r"<title>[^<]+</title>", s)) == 1, "S1 one <title>")
    for pat in (r'<meta name="description" content="[^"]{60,160}"', r'<link rel="canonical" href="%s"' % re.escape(URL),
                r'<meta property="og:url" content="%s"' % re.escape(URL), r'<meta name="robots" content="index, follow">',
                r'"datePublished": "\d{4}-\d\d-\d\d"', r'"dateModified": "\d{4}-\d\d-\d\d"'):
        need(re.search(pat, s), "S1 missing: " + pat)
    need("noindex" not in s and "pn-preview-band" not in s and "Private preview" not in s,
         "S1 a preview marker is left (noindex or preview band)")
    # S2
    blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', s, re.S)
    need(blocks, "S2 no JSON-LD")
    for b in blocks:
        try:
            j = json.dumps(json.loads(b))
        except ValueError as e:
            problems.append("S2 JSON-LD does not parse: %s" % e); continue
        for bad in ('"Product"', '"Offer"', '"price"', '"LocalBusiness"', '"Review"', '"FAQPage"', '"AggregateOffer"'):
            need(bad not in j, "S2 unsupported structured data: " + bad)
    # S3
    need(len(re.findall(r"<h1[\s>]", s)) == 1 and "<h1>The Home You Build</h1>" in s, "S3 exactly one H1, the title")
    need(QUESTION in s, "S3 the hero question")
    need("pn-hero-compare__mtitle" not in nocom, "S3 a compact title repeats the heading above the image")
    # S4
    refs = set(re.findall(r'(?:href|src)="([^"#?]+)', nocom)) | {
        u.strip().split(" ")[0] for ss in re.findall(r'(?:srcset|imagesrcset)="([^"]+)"', nocom) for u in ss.split(",")}
    for ref in refs:
        if ref.startswith(("http:", "https:", "mailto:", "tel:", "data:", "/")) or not ref:
            continue
        need(files(ref), "S4 local reference does not resolve: " + ref)
    # S5
    hero = re.search(r'<header class="d-hero[^"]*\bpn-hero-compare--std\b[^"]*">(.*?)</header>', s, re.S)
    h5 = hero.group(1) if hero else ""
    need(hero and "hy-hero" in hero.group(0)[:90], "S5 the standard slider hero")
    need('href="assets/identity/pn-compare.css?v=' in s and 'src="assets/identity/pn-compare.js?v=' in s, "S5 the shared slider stylesheet and script")
    need(re.search(r'<figure class="pn-compare pn-compare--hero" id="hyHeroCompare" data-start="100"', h5)
         and re.search(r'class="pn-compare__range" type="range" min="0" max="100" step="1" value="100"', h5), "S5 the slider opens at 100% BEFORE")
    for role, layer in (("BEFORE", "before"), ("POSSIBLE", "possible")):
        pc = re.search(r'<div class="pn-compare__%s">\s*<picture>(.*?)</picture>' % layer, h5, re.S)
        body = pc.group(1) if pc else ""
        need(("assets/disc040/img/DISC-040-%s-1024.jpg" % role) in body and ("DISC-040-%s-M-753.webp 753w" % role) in body
             and ("DISC-040-%s-1536.webp 1536w" % role) in body and 'width="1670" height="941"' in body,
             "S5 the %s layer, its phone copy and its true dimensions" % role)
        alt = re.search(r'alt="([^"]*)"', body)
        need(alt and alt.group(1).startswith(role.capitalize() + ":") and len(alt.group(1)) >= 60 and "AI-generated" in alt.group(1),
             "S5 the %s layer needs its descriptive, disclosing alt" % role)
        if role == "BEFORE":
            need('fetchpriority="high"' in body, "S5 BEFORE, seen first, is the priority image")
    need('<p class="pn-compare__tag is-before" aria-hidden="true">Before</p>' in h5 and '<p class="pn-compare__tag is-possible" aria-hidden="true">Possible</p>' in h5,
         "S5 the Before and Possible tags")
    need('aria-describedby="hyHeroCompareKeys"' in h5 and 'id="hyHeroCompareKeys"' in h5 and 'class="pn-compare__jump" role="group"' in h5,
         "S5 the keyboard help and the jump group")
    need('<p class="pn-compare__note">%s</p>' % AI in h5, "S5 the hero AI disclosure")
    need(re.search(r'</header>\n<p class="pn-hero-note pn-hero-note--inset"[^>]*>%s</p>' % re.escape(AI), s), "S5 the desktop AI disclosure beneath the hero")
    need('<meta property="og:image" content="https://plotnua.ie/assets/disc040/img/DISC-040-og-1200x630.jpg">' in s, "S5 the share image")
    # S6
    ks = re.findall(r'<div class="lg-chapter" id="lg-ch0(\d)">.*?<p class="lg-kicker">([^<]+)</p>', s)
    need([k for k, _t in ks] == list("123456"), "S6 six chapters in order: %s" % [k for k, _t in ks])
    need([html.unescape(t) for _k, t in ks] == CHAPTERS, "S6 the approved chapter kickers: %s" % [t for _k, t in ks])
    # S7
    ch2 = re.search(r'id="lg-ch02".*?id="lg-ch03"', s, re.S)
    dg = re.search(r'<figure class="or-diagram[^"]*">(.*?)</figure>', ch2.group(0) if ch2 else "", re.S)
    db = dg.group(1) if dg else ""
    need('id="hyWallsT"' in db and 'id="hyWallsD"' in db and "NOT TO SCALE" in db, "S7 the wall-section diagram, labelled and not to scale")
    # S8
    for must in ("PlotNua has no confirmed commercial relationship with the companies listed",
                 "Irish availability, installation arrangements and final prices would need to be established directly with each supplier",
                 "Inclusion is not a recommendation", "it doesn’t mean the company won’t supply Ireland",
                 "We have no confirmed commercial relationship with any house maker named on this page",
                 "we are not an agent, distributor or builder"):
        need(must in flat, "S8 maker qualification missing: " + must)
    for bad in ("authorised distributor", "authorized distributor", "official distributor", "exclusive irish", "certified installer",
                "our partner", "partnered with", "endorsed by", "approved installer", "we install", "we supply", "recommended maker"):
        need(bad not in low, "S8 distributor or endorsement wording: " + bad)
    # S9
    for must in ("It is still a draft", "the 2005 rural housing guidelines", "opt out of statutory certification",
                 "still requires stage reports and a final certificate of compliance", "not legal, financial or professional advice"):
        need(must in flat, "S9 regulatory caution missing: " + must)
    for bad in ("no planning permission needed", "does not need planning", "always exempt", "guaranteed exempt", "no permission required",
                "guaranteed planning"):
        need(bad not in low, "S9 blanket exemption wording: " + bad)
    # S10
    for must in ("These are insurance minimums for typical estate-type houses, not quotes for a self-build",
                 "An average would hide more than it shows, so we don’t give one",
                 "Not independently verified; not a promise for any site",
                 "We’ll publish ranges only where enough evidence meets our pricing rules"):
        need(must in flat, "S10 figure qualification missing: " + must)
    for bad in ("average cost of building", "typical cost", "costs around", "costs about", "you will save", "guaranteed price"):
        need(bad not in low, "S10 cost-estimate wording: " + bad)
    # S11
    need(not re.search(r"<(form|select|textarea)\b", s), "S11 a form or form control is present")
    inputs = re.findall(r"<input\b[^>]*>", s)
    need(len(inputs) == 2 and any('class="pns-input"' in i and 'type="search"' in i for i in inputs)
         and any('class="pn-compare__range"' in i and 'type="range"' in i for i in inputs),
         "S11 an input other than the site search and the slider range: %s" % [i[:60] for i in inputs])
    need("PlotNua is free for homeowners" in flat and "we don’t take orders, deposits or quote requests for houses" in flat,
         "S11 the status statement is missing")
    page_only = re.sub(r"<!-- PLOTNUA HEADER v2 · (BAR|ROW) · BEGIN.*?<!-- PLOTNUA HEADER v2 · \1 · END -->", "", s, flags=re.S)
    need(page_only.count("PLOTNUA HEADER v2") == 0 and s.count("PLOTNUA HEADER v2") == 4, "S11 the header blocks are not exactly the generated pair")
    for bad in ("fetch(", "xmlhttprequest", "sendbeacon", "workers.dev", "formspree", "airtable", "wa.me/", "api.whatsapp"):
        need(bad not in page_only.lower(), "S11 data collection or enquiry routing: " + bad)
    return problems


def main():
    s = read(PAGE)
    files = lambda p: os.path.exists(os.path.join(ROOT, p))
    problems = check(s, files)

    def need(cond, msg):
        if not cond:
            problems.append(msg)

    # S13 containment and wiring
    sm, idx, lib, ext = read("sitemap.xml"), read("search-index-v1.json"), read("discoveries.html"), read("discovery-extend-the-house.html")
    tm = json.loads(read("atlas-tools/search-topic-map.json"))
    need(sm.count("<loc>https://plotnua.ie/%s</loc>" % PAGE) == 1, "S13 not exactly one sitemap entry")
    recs = [r for r in json.loads(idx)["records"] if r.get("route") == PAGE]
    need(len(recs) == 1 and recs[0].get("type") == "possibility", "S13 not exactly one Search possibility record for the page")
    need(not [e for e in tm["entries"] if PAGE in e.get("targets", [])], "S13 a governed search phrase targets the page (none approved)")
    cards = re.findall(r'<a class="lib-card" href="%s" data-cat="([^"]+)">(.*?)</a>' % re.escape(PAGE), lib, re.S)
    need(len(cards) == 1 and cards[0][0] == "Space" and "assets/disc040/img/DISC-040-POSSIBLE-1024.jpg" in cards[0][1]
         and '<span class="lib-aichip">AI-generated illustration</span>' in cards[0][1] and "BEFORE" not in cards[0][1],
         "S13 the Library card (one, Space, the POSSIBLE copy, with the AI chip)")
    need(ext.count('href="%s"' % PAGE) == 1, "S13 the inbound link from Extend the House")
    # S14 provenance by hash
    reg = json.loads(read("image-provenance-records.json"))
    masters = {r["asset"]: r for r in reg["records"]}
    derivs = {d["asset"]: d for d in reg["derivatives"]}
    used = set(re.findall(r'assets/disc040/img/DISC-040-[A-Za-z0-9-]+\.(?:webp|jpg|png)', s + lib))
    need(len(used) >= 13, "S14 the DISC-040 images in use (%d)" % len(used))
    sha = lambda a: hashlib.sha256(open(os.path.join(ROOT, a), "rb").read()).hexdigest()
    for a in sorted(used):
        d = derivs.get(a); src = (d or {}).get("derived_from", {}); m = masters.get(src.get("asset"))
        need(d and m and m.get("class") == "AI_ILLUSTRATION", "S14 %s is not a recorded derivative of a declared AI master" % a)
        need(m and "discovery" in m.get("permitted_surfaces", []), "S14 %s: its master does not permit the discovery surface" % a)
        need(d and files(a) and sha(a) == d["sha256"], "S14 %s differs from its recorded derivative" % a)
        need(m and src.get("sha256") == m["sha256"] and sha(m["asset"]) == m["sha256"], "S14 %s: its master is not the declared, unchanged file" % a)
    card_src = derivs.get("assets/disc040/img/DISC-040-POSSIBLE-1024.jpg", {}).get("derived_from", {}).get("asset")
    need("library-card" in masters.get(card_src, {}).get("permitted_surfaces", []), "S14 the Library card's master does not permit library-card")
    need("POSSIBLE" in derivs.get("assets/disc040/img/DISC-040-og-1200x630.jpg", {}).get("derived_from", {}).get("asset", ""),
         "S14 the share image is made from the POSSIBLE")

    if "--self-test" in sys.argv:
        faults = {
            "S1": s.replace('<meta name="robots" content="index, follow">', '<meta name="robots" content="noindex, nofollow">', 1),
            "S1 ": s.replace("<body ", '<body data-x="1" ', 1).replace("</body>", '<div class="pn-preview-band">Private preview</div></body>', 1),
            "S2": s.replace('"@type": "WebPage"', '"@type": "WebPage", "price": "1"', 1),
            "S3": s.replace("<h1>The Home You Build</h1>", "<h1>The Home You Build</h1><h1>x</h1>", 1),
            "S4": s.replace('src="assets/disc036/img/DISC-036-POSSIBLE-1024.jpg"', 'src="assets/disc036/img/missing.jpg"', 1),
            "S5": s.replace('id="hyHeroCompare" data-start="100"', 'id="hyHeroCompare" data-start="50"', 1),
            "S5 ": s.replace('<p class="pn-compare__note">%s</p>' % AI, '<p class="pn-compare__note"></p>', 1),
            "S6": s.replace('<p class="lg-kicker">Make it happen</p>', '<p class="lg-kicker">Buy now</p>', 1),
            "S7": s.replace('<figure class="or-diagram reveal">', '<figure class="gone">', 1),
            "S8": s.replace("Inclusion is not a recommendation", "PlotNua is the authorised distributor", 1),
            "S8 ": s.replace("we are not an agent, distributor or builder", "we are their partner", 1),
            "S9": s.replace("It is still a draft", "It is now law", 1),
            "S9 ": s.replace("still requires stage reports and a final certificate of compliance", "accepts the opt-out", 1),
            "S10": s.replace("These are insurance minimums for typical estate-type houses, not quotes for a self-build", "A self-build costs about this", 1),
            "S10 ": s.replace("Not independently verified; not a promise for any site", "Guaranteed", 1),
            "S11": s.replace('<div class="rg-panel reveal">', '<form><textarea name="m"></textarea></form><div class="rg-panel reveal">', 1),
            "S11 ": s.replace('<div class="rg-panel reveal">', '<a href="https://wa.me/353000000000?text=HY">WhatsApp us</a><div class="rg-panel reveal">', 1),
            "S11  ": s.replace('<div class="rg-panel reveal">', '<script>fetch("https://x.workers.dev/i")</script><div class="rg-panel reveal">', 1),
        }
        missed = [k for k, t in faults.items() if not any(p.startswith(k.strip() + " ") for p in check(t, files))]
        print("DISC-040 PAGE · SELF-TEST " + ("OK (%d planted faults caught)" % len(faults) if not missed else "MISSED %s" % missed))
        if missed:
            sys.exit(1)
    if problems:
        print("DISC-040 PAGE · FAILED")
        for p in problems:
            print("  " + p)
        sys.exit(1)
    print("DISC-040 PAGE · OK (S1-S14)")


if __name__ == "__main__":
    main()
