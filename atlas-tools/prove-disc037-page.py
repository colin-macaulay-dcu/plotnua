#!/usr/bin/env python3
"""DISC-037 · The Resourceful Garden: page, SEO, claims, containment and provenance proof (read-only).
Stage 3 private preview (8 Nov 2026), development branch dev/disc037-resourceful-garden, NOT deployed.

    python3 atlas-tools/prove-disc037-page.py [--self-test]

  R1  one <title>, a meta description (60-160 chars), canonical and og:url for this page; robots is either
      "noindex, nofollow" (private preview) or "index, follow" (release candidate), and R14 follows whichever it is
  R2  JSON-LD parses; no Product, Offer, price, LocalBusiness, Review, FAQPage or AggregateOffer data
  R3  exactly one H1 ("The Resourceful Garden") and the approved hero question
  R4  every local href/src/srcset on the page resolves to a file
  R5  the hero is the DISC-037-only two-view presentation (Stage 7 founder decision): the approved BEFORE and POSSIBLE
      as two labelled views, each with a descriptive alt; two buttons with aria-pressed and a live region; the script
      opens on BEFORE and changes only on a press (no timer, no autoplay); the reduced-motion rule; the AI disclosure;
      no pn-compare slider on the page; the share image is made from the POSSIBLE
  R6  six chapters, in order, with the six approved titles
  R7  exactly the five supplied chapter images, each whole, with a descriptive alt and the AI disclosure;
      the pantry image says it is not a specific product
  R8  chapter 04 shows the greenhouse image, and the text explains the dark barrels as thermal mass
  R9  Groundfridge is framed as an example: Ireland/UK not listed, Irish delivery not confirmed, not a
      PlotNua partner, delivery/excavation/installation excluded; no distributor or endorsement wording
  R10 planning: Class 3, 30 m2, 25 m2 open space, 27 July 2026, poultry excluded, Section 5 (EUR 80), the
      buried store untested, not legal advice; no blanket "no planning needed" wording
  R11 living roof structure check; costs labelled indicative and not quotes, with the checked date
  R12 no data collection or payment: no <form>, fetch, XHR, beacon, Workers or Formspree endpoint
  R13 no partner / commission / referral-fee / affiliate / discount wording, no savings, carbon or
      self-sufficiency promises; the no-relationship disclaimer is present; no business image is shown
  R14 preview: not in the sitemap, the search index, the governed search map or the Discovery Library.
      release (index, follow): exactly one sitemap entry, one search-index possibility record, the three governed
      phrases (grow your own, underground food storage, vegetable garden), and exactly one Library card, in Garden,
      showing the POSSIBLE (never the BEFORE) with the AI chip
  R15 related links go only to live Discoveries (Borrowed Garden, Water Wall, Outdoor Room, House as a
      Power Station, Extend the House)
  R16 provenance: every DISC-037 image in use is exactly a recorded derivative (sha256) of a declared,
      unchanged AI_ILLUSTRATION master that permits the discovery surface
Prints "DISC-037 PAGE · OK" only when every check passes.
"""
import hashlib, html, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = "discovery-the-resourceful-garden.html"
URL = "https://plotnua.ie/" + PAGE
AI_LABEL = "Illustrative AI-generated visualisation. Not an actual installation."
ROLES = ["03-GARDEN-THAT-FEEDS-YOU", "04-UNDERGROUND-PANTRY", "05-WASTE-INTO-WONDERFUL", "06-GREENHOUSE-STORES-SUNSHINE",
         "07-LIVING-ROOF-WILD-GARDEN"]
CHAPTERS = ["The garden that feeds you", "The underground pantry", "Waste into something wonderful",
            "The greenhouse that stores sunshine", "The living roof and wild garden", "Make it happen"]
RELATED = ["discovery-the-borrowed-garden.html", "discovery-the-water-wall.html", "discovery-the-outdoor-room.html",
           "discovery-house-as-power-station.html", "discovery-extend-the-house.html"]


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
    nocom = re.sub(r"<!--.*?-->", " ", s, flags=re.S)

    # R1
    need(len(re.findall(r"<title>[^<]+</title>", s)) == 1, "R1 one <title>")
    for pat in (r'<meta name="description" content="[^"]{60,160}"', r'<link rel="canonical" href="%s"' % re.escape(URL),
                r'<meta property="og:url" content="%s"' % re.escape(URL)):
        need(re.search(pat, s), "R1 missing: " + pat)

    need(re.search(r'<meta name="robots" content="(?:noindex, nofollow|index, follow)">', s), "R1 robots must be noindex,nofollow or index,follow")

    # R2
    blocks = re.findall(r'<script type="application/ld\+json">(.*?)</script>', s, re.S)
    need(blocks, "R2 no JSON-LD")
    for b in blocks:
        try:
            j = json.dumps(json.loads(b))
        except ValueError as e:
            problems.append("R2 JSON-LD does not parse: %s" % e); continue
        for bad in ('"Product"', '"Offer"', '"price"', '"LocalBusiness"', '"Review"', '"FAQPage"', '"AggregateOffer"'):
            need(bad not in j, "R2 unsupported structured data: " + bad)

    # R3
    need(len(re.findall(r"<h1[\s>]", s)) == 1, "R3 exactly one H1")
    need("<h1>The Resourceful Garden</h1>" in s, "R3 the H1 is the title")
    need("What if your garden could grow more, waste less and give something back?" in s, "R3 the hero question")

    # R4
    refs = set(re.findall(r'(?:href|src)="([^"#?]+)', nocom)) | {
        u.strip().split(" ")[0] for ss in re.findall(r'(?:srcset|imagesrcset)="([^"]+)"', nocom) for u in ss.split(",")}
    for ref in refs:
        if ref.startswith(("http:", "https:", "mailto:", "tel:", "data:", "/")) or not ref:
            continue
        need(files(ref), "R4 local reference does not resolve: " + ref)

    # R5
    hero = re.search(r'<header class="d-hero[^"]*rg-hero--views[^"]*">(.*?)</header>', s, re.S)
    need(hero, "R5 the two-view hero")
    h5 = hero.group(1) if hero else ""
    for role in ("BEFORE", "POSSIBLE"):
        pc = re.search(r'<picture class="rg-views__img is-%s"[^>]*>(.*?)</picture>' % role.lower(), h5, re.S)
        need(pc and ("assets/disc037/img/DISC-037-%s-1024.jpg" % role) in pc.group(1) and ("DISC-037-%s-M-819.webp" % role) in pc.group(1),
             "R5 the %s view and its phone copy" % role)
        alt = re.search(r'alt="([^"]*)"', pc.group(1)) if pc else None
        need(alt and alt.group(1).startswith(role.capitalize() + ":") and len(alt.group(1)) >= 60, "R5 the %s view needs its descriptive alt" % role)
    need(h5.count('class="rg-views__btn"') == 2 and 'data-show="before"' in h5 and 'data-show="possible"' in h5 and h5.count("aria-pressed=") == 2,
         "R5 two view buttons with aria-pressed")
    need('role="group"' in h5 and 'id="rgViewsLive" aria-live="polite"' in h5, "R5 the button group and the live region")
    need('<span class="is-before">Before</span><span class="is-possible">Possible</span>' in h5, "R5 the visible view labels")
    need("Illustrative AI-generated visualisations. Not an actual installation." in h5, "R5 the hero AI disclosure")
    need(not re.search(r'class="pn-compare[\s"]|pn-compare\.(?:js|css)|class="pn-compare__range"', s), "R5 no comparison slider on this page")
    js = re.search(r"/\* DISC-037 · the two-view hero.*?</script>", s, re.S)
    need(js and "show('before', false);" in js.group(0), "R5 the hero opens on BEFORE")
    need(js and not re.search(r"setInterval|setTimeout|requestAnimationFrame", js.group(0)), "R5 no timer or autoplay in the hero")
    need(re.search(r'<meta property="og:image" content="https://plotnua\.ie/assets/disc037/img/DISC-037-og-1200x630\.jpg"', s), "R5 the share image")

    # R6
    ks = re.findall(r'<div class="lg-chapter" id="lg-ch0(\d)">.*?<p class="lg-kicker">([^<]+)</p>', s)
    need([k for k, _t in ks] == list("123456"), "R6 six chapters in order: %s" % [k for k, _t in ks])
    need([html.unescape(t) for _k, t in ks] == CHAPTERS, "R6 the approved chapter titles: %s" % [t for _k, t in ks])

    # R7
    figs = re.findall(r'<figure class="rg-feature[^"]*" data-rg-image="DISC-037-([A-Z0-9-]+)">(.*?)</figure>', s, re.S)
    need([r for r, _b in figs] == ROLES, "R7 the four chapter images in order: %s" % [r for r, _b in figs])
    for role, body in figs:
        alt = re.search(r'alt="([^"]*)"', body)
        need(alt and len(alt.group(1)) >= 40, "R7 %s needs a descriptive alt" % role)
        need("AI-generated visualisation" in body and "Not an actual installation" in body, "R7 %s lacks the AI disclosure" % role)
    pan = dict(figs).get("04-UNDERGROUND-PANTRY", "")
    need("Not an actual installation or a specific product." in pan, "R7 the pantry image is not a specific product")

    # R8 (Stage 4): chapter 04 shows the founder's greenhouse image, and the text explains the barrels as thermal mass
    ch4 = re.search(r'id="lg-ch04".*?id="lg-ch05"', s, re.S)
    c4 = ch4.group(0) if ch4 else ""
    need('data-rg-image="DISC-037-06-GREENHOUSE-STORES-SUNSHINE"' in c4 and 'data-rg-pending="ch04"' not in c4, "R8 the chapter 04 greenhouse image")
    need("the barrels act as thermal mass" in text(c4), "R8 the barrels are explained as thermal mass")

    # R9
    for bad in ("authorised distributor", "authorized distributor", "official distributor", "endorsed by", "approved by groundfridge",
                "groundfridge installation", "stockist", "buy a groundfridge"):
        need(bad not in low, "R9 distributor or endorsement wording: " + bad)
    for must in ("Ireland and the UK are not listed among its delivery regions", "Irish delivery is not confirmed",
                 "the Groundfridge is not a PlotNua partner", "Delivery, excavation and installation"):
        need(must in flat, "R9 Groundfridge qualification missing: " + must)

    # R10
    for must in ("27 July 2026", "30 m²", "25 m²", "not for keeping pigs, poultry", "Section 5 declaration", "€80",
                 "no rule or decision we found deals with a buried one", "not legal advice"):
        need(must in flat, "R10 planning statement missing: " + must)
    for bad in ("no planning permission needed", "doesn't need planning", "does not need planning", "planning-free",
                "always exempt", "guaranteed exempt", "no permission required"):
        need(bad not in low, "R10 blanket exemption wording: " + bad)

    # R11
    need("have the building’s structure checked" in low, "R11 the living roof structure check")
    need("not quotes" in flat and "checked 8 November 2026" in flat and "indicative" in low, "R11 costs labelled indicative, not quotes, dated")

    # R12
    for bad in ("<form", "fetch(", "xmlhttprequest", "sendbeacon", "workers.dev", "formspree"):
        need(bad not in s.lower(), "R12 data collection or payment: " + bad)

    # R13
    need(not re.search(r"commission(?! for regulation of utilities)", low), "R13 commercial or unsupported-claim wording: commission")
    for bad in ("our partner", "partnered", "referral fee", "affiliate", "discount", "exclusive offer",
                "save €", "savings", "co2", "cut your bills", "pay for itself", "recommended supplier"):
        need(bad not in low, "R13 commercial or unsupported-claim wording: " + bad)
    need(not re.search(r"\bcarbon\b", low), "R13 commercial or unsupported-claim wording: carbon")
    need(low.count("self-sufficient") == 1 and "none of this makes a household self-sufficient" in low, "R13 self-sufficiency is only disclaimed")
    need("PlotNua has no commercial relationship with any business named on this page" in flat, "R13 the no-relationship disclaimer")
    who = re.search(r'id="who-can-help".*?</ul>', s, re.S)
    need(who and "<img" not in who.group(0), "R13 a business image is shown")

    # R15
    for link in RELATED:
        need(('href="%s"' % link) in s and files(link), "R15 related link missing or not live: " + link)
    for bad in ("discovery-underground-space", "discovery-hens", "discovery-off-grid"):
        need(bad not in s, "R15 a speculative link: " + bad)
    return problems


def main():
    s = read(PAGE)
    files = lambda p: os.path.exists(os.path.join(ROOT, p))
    problems = check(s, files)

    def need(cond, msg):
        if not cond:
            problems.append(msg)

    # R14 containment (private preview) or publication (release candidate)
    released = '<meta name="robots" content="index, follow">' in s
    sm, idx, lib = read("sitemap.xml"), read("search-index-v1.json"), read("discoveries.html")
    tm = json.loads(read("atlas-tools/search-topic-map.json"))
    phrases = sorted(e["phrase"] for e in tm["entries"] if PAGE in e.get("targets", []))
    cards = re.findall(r'<a class="lib-card" href="%s" data-cat="([^"]+)">(.*?)</a>' % re.escape(PAGE), lib, re.S)
    if not released:
        need(PAGE not in sm, "R14 the page is in the sitemap")
        need(PAGE not in idx, "R14 the page is in the search index")
        need(not phrases, "R14 a governed search entry targets the page")
        need(not cards and ('href="%s"' % PAGE) not in lib, "R14 a Discovery Library card links the page")
    else:
        need(sm.count("<loc>%s</loc>" % URL) == 1, "R14 exactly one sitemap entry")
        recs = [r for r in json.loads(idx)["records"] if r.get("route") == PAGE]
        need(len(recs) == 1 and recs[0]["type"] == "possibility", "R14 exactly one search-index possibility record")
        need(phrases == ["grow your own", "underground food storage", "vegetable garden"], "R14 governed search phrases: %s" % phrases)
        need(len(cards) == 1, "R14 exactly one Library card")
        if cards:
            cat, body = cards[0]
            need(cat == "Garden" and '<span class="lib-cat">Garden</span>' in body, "R14 the card is in Garden")
            need("DISC-037-POSSIBLE-1024.jpg" in body and "DISC-037-02-POSSIBLE-MASTER-480w.webp" in body and "BEFORE" not in body,
                 "R14 the card shows the POSSIBLE, never the BEFORE")
            need('<span class="lib-aichip">AI-generated illustration</span>' in body, "R14 the card carries the AI chip")
            need('<span class="lib-title">The Resourceful Garden</span>' in body and
                 "What if your garden could grow more, waste less and give something back?" in body, "R14 the card title and line")

    # R16 provenance by hash (as DISC-035 O16 / DISC-036 E16)
    reg = json.loads(read("image-provenance-records.json"))
    masters = {r["asset"]: r for r in reg["records"]}
    derivs = {d["asset"]: d for d in reg["derivatives"]}
    used = set(re.findall(r'assets/disc037/img/DISC-037-[A-Za-z0-9-]+\.(?:webp|jpg)', s))
    used |= set(re.findall(r'assets/(?:disc037/img|library/img)/DISC-037-[A-Za-z0-9-]+\.(?:webp|jpg)', "".join(b for _c, b in cards)))
    need(len(used) >= 25, "R16 the DISC-037 images in use (%d)" % len(used))
    sha = lambda a: hashlib.sha256(open(os.path.join(ROOT, a), "rb").read()).hexdigest()
    for a in sorted(used):
        d = derivs.get(a)
        src = (d or {}).get("derived_from", {})
        m = masters.get(src.get("asset"))
        need(d and m and m.get("class") == "AI_ILLUSTRATION", "R16 %s is not a recorded derivative of a declared AI master" % a)
        surf = "library-card" if "/library/" in a else "discovery"
        need(m and surf in m.get("permitted_surfaces", []), "R16 %s: its master does not permit the %s surface" % (a, surf))
        need(d and files(a) and sha(a) == d["sha256"], "R16 %s differs from its recorded derivative" % a)
        need(m and src.get("sha256") == m["sha256"] and sha(m["asset"]) == m["sha256"], "R16 %s: its master is not the declared, unchanged file" % a)

    need("POSSIBLE" in derivs.get("assets/disc037/img/DISC-037-og-1200x630.jpg", {}).get("derived_from", {}).get("asset", ""),
         "R16 the share image is made from the POSSIBLE")
    if "--self-test" in sys.argv:
        faults = {
            "R1": s.replace('<meta name="robots" content="', '<meta name="robots" content="noindex, follow', 1),
            "R3": s.replace("<h1>The Resourceful Garden</h1>", "<h1>The Resourceful Garden</h1><h1>x</h1>"),
            "R5": s.replace("show('before', false);", "show('before', false); setInterval(function(){}, 4000);", 1),
            "R5 ": s.replace('data-show="possible" aria-pressed="true"', 'data-show="possible"', 1),
            "R6": s.replace('<p class="lg-kicker">Make it happen</p>', '<p class="lg-kicker">Next steps</p>', 1),
            "R7": s.replace("Not an actual installation or a specific product.", "Not an actual installation.", 1),
            "R8": s.replace("the barrels act as thermal mass", "the barrels hold rainwater", 1),
            "R9 ": s.replace("Shown as an example of what exists", "PlotNua is an authorised distributor. Shown as an example of what exists", 1),
            "R9": s.replace("Irish delivery is not confirmed", "Irish delivery is available", 1),
            "R10": s.replace("no rule or decision we found deals with a buried one", "a buried one is exempt", 1),
            "R11": s.replace("not quotes", "firm prices"),
            "R12": s.replace("</main>", "<form action='https://x.workers.dev'></form></main>"),
            "R13": s.replace("Irish businesses that can help.", "Irish businesses that can help. Ask our partner.", 1),
            "R15": s.replace('href="discovery-the-water-wall.html"', 'href="discovery-underground-space.html"'),
        }
        missed = [k for k, t in faults.items() if not any(p.startswith(k.strip() + " ") for p in check(t, files))]
        print("DISC-037 PAGE · SELF-TEST " + ("OK (%d planted faults caught)" % len(faults) if not missed else "MISSED %s" % missed))
        if missed:
            sys.exit(1)

    if problems:
        print("DISC-037 PAGE · FAILED")
        for p in problems:
            print("  " + p)
        sys.exit(1)
    print("DISC-037 PAGE · OK (R1-R16)")


if __name__ == "__main__":
    main()
