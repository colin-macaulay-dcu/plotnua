#!/usr/bin/env python3
"""DISC-038 · The Hidden Shelter: page, claims, containment and provenance proof (read-only).
Stage 4 private preview (8 Nov 2026), branch dev/disc038-hidden-shelter, NOT deployed. Modelled on prove-disc037-page.py.

    python3 atlas-tools/prove-disc038-page.py [--self-test]

  S1  one <title>, a meta description (60-160 chars), canonical and og:url; robots "noindex, nofollow" (private preview)
  S2  JSON-LD parses; no Product, Offer, price, LocalBusiness, Review, FAQPage or AggregateOffer data
  S3  exactly one H1 ("The Hidden Shelter") and the approved hero question; no compact title above the image
  S4  every local href/src/srcset resolves to a file
  S5  the standard pn-compare hero: shared stylesheet and script, opening at 100% BEFORE, the founder's pair (hero and phone
      copies) with descriptive alts, BEFORE the priority image, tags, keyboard help, jump group, the approved AI disclosure
      in the figure and directly beneath the hero; the share image is the POSSIBLE
  S6  six chapters, in order, with the six approved titles
  S7  the chapter 02 section illustration is kept, with a descriptive alt and its AI disclosure
  S8  supplier qualifications: no confirmed Irish supply, not a partner, no agreement, not a recommendation; no distributor,
      installer, certification, guarantee or endorsement wording
  S9  planning and feasibility cautions: Class 3 excludes habitation, 30 m2, Section 5 (EUR 80), not legal advice,
      groundwater, radon; no blanket exemption wording
  S10 prices are advertised international prices, exclude delivery and installation, no maker has quoted, checked date
  S11 the register-interest form is inert: no action, every control inside a disabled fieldset, the preview notice;
      no fetch, XHR, beacon, Workers, Formspree, Airtable or WhatsApp enquiry link
  S12 protection is never promised: "Features are not protection" and "No guarantees" present; no "guaranteed safe",
      "bomb-proof", "nuclear-proof", "fully protected" wording
  S13 containment: not in the sitemap, the search index, the governed search map or the Discovery Library
  S14 provenance: every DISC-038 image in use is exactly a recorded derivative (sha256) of a declared, unchanged
      AI_ILLUSTRATION master that permits the discovery surface
Prints "DISC-038 PAGE · OK" only when every check passes.
"""
import hashlib, html, json, os, re, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = "discovery-the-hidden-shelter.html"
URL = "https://plotnua.ie/" + PAGE
AI = "Illustrative AI-generated visualisation. Not an actual installation."
CHAPTERS = ["The new shelter age", "Life below ground", "The engineering behind protection", "The international market",
            "Could it work in Ireland?", "Explore the possibility"]


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
                r'<meta property="og:url" content="%s"' % re.escape(URL), r'<meta name="robots" content="noindex, nofollow">'):
        need(re.search(pat, s), "S1 missing: " + pat)
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
    need(len(re.findall(r"<h1[\s>]", s)) == 1 and "<h1>The Hidden Shelter</h1>" in s, "S3 exactly one H1, the title")
    need("What if your family had a place to retreat when the unexpected happens?" in s, "S3 the hero question")
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
    need(hero and "hs-hero" in hero.group(0)[:90], "S5 the standard slider hero")
    need('href="assets/identity/pn-compare.css?v=' in s and 'src="assets/identity/pn-compare.js?v=' in s, "S5 the shared slider stylesheet and script")
    need(re.search(r'<figure class="pn-compare pn-compare--hero" id="hsHeroCompare" data-start="100"', h5)
         and re.search(r'class="pn-compare__range" type="range" min="0" max="100" step="1" value="100"', h5), "S5 the slider opens at 100% BEFORE")
    for role, layer in (("BEFORE", "before"), ("POSSIBLE", "possible")):
        pc = re.search(r'<div class="pn-compare__%s">\s*<picture>(.*?)</picture>' % layer, h5, re.S)
        body = pc.group(1) if pc else ""
        need(("assets/disc038/img/DISC-038-%s-1024.jpg" % role) in body and ("DISC-038-%s-M-819.webp" % role) in body
             and ("DISC-038-%s-1536.webp 1536w" % role) in body, "S5 the %s layer and its phone copy" % role)
        alt = re.search(r'alt="([^"]*)"', body)
        need(alt and alt.group(1).startswith(role.capitalize() + ":") and len(alt.group(1)) >= 60 and "AI-generated" in alt.group(1),
             "S5 the %s layer needs its descriptive, disclosing alt" % role)
        if role == "BEFORE":
            need('fetchpriority="high"' in body, "S5 BEFORE, seen first, is the priority image")
    need('<p class="pn-compare__tag is-before" aria-hidden="true">Before</p>' in h5 and '<p class="pn-compare__tag is-possible" aria-hidden="true">Possible</p>' in h5,
         "S5 the Before and Possible tags")
    need('aria-describedby="hsHeroCompareKeys"' in h5 and 'id="hsHeroCompareKeys"' in h5 and 'class="pn-compare__jump" role="group"' in h5,
         "S5 the keyboard help and the jump group")
    need('<p class="pn-compare__note">%s</p>' % AI in h5, "S5 the hero AI disclosure")
    need(re.search(r'</header>\n<p class="pn-hero-note pn-hero-note--inset"[^>]*>%s</p>' % re.escape(AI), s), "S5 the desktop AI disclosure beneath the hero")
    need('<meta property="og:image" content="https://plotnua.ie/assets/disc038/img/DISC-038-og-1200x630.jpg">' in s, "S5 the share image")
    # S6
    ks = re.findall(r'<div class="lg-chapter" id="lg-ch0(\d)">.*?<p class="lg-kicker">([^<]+)</p>', s)
    need([k for k, _t in ks] == list("123456"), "S6 six chapters in order: %s" % [k for k, _t in ks])
    need([html.unescape(t) for _k, t in ks] == CHAPTERS, "S6 the approved chapter titles: %s" % [t for _k, t in ks])
    # S7
    ch2 = re.search(r'id="lg-ch02".*?id="lg-ch03"', s, re.S)
    sec = re.search(r'<figure class="hs-section[^"]*">(.*?)</figure>', ch2.group(0) if ch2 else "", re.S)
    sb = sec.group(1) if sec else ""
    need("DISC-038-SECTION-1024.jpg" in sb and "DISC-038-SECTION-1536.webp" in sb, "S7 the chapter 02 section illustration")
    alt = re.search(r'alt="([^"]*)"', sb)
    need(alt and len(alt.group(1)) >= 60, "S7 the section illustration needs a descriptive alt")
    need("AI-generated illustration" in sb and "Not to scale" in sb and "not a specific product or installation" in sb, "S7 the section illustration lacks its AI disclosure")
    # S8
    for must in ("None of these companies has confirmed that it supplies or installs in Ireland", "None is a PlotNua partner",
                 "PlotNua has no agreement with any of them", "inclusion is not a recommendation",
                 "we are not a distributor or an installer", "Burrowed is not a PlotNua partner"):
        need(must in flat, "S8 supplier qualification missing: " + must)
    for bad in ("authorised distributor", "authorized distributor", "official distributor", "exclusive irish", "certified installer",
                "our partner", "partnered with", "endorsed by", "approved installer", "we install", "we supply"):
        need(bad not in low, "S8 distributor or endorsement wording: " + bad)
    # S9
    for must in ("not for human habitation", "30 m2", "Section 5 declaration", "€80", "not legal or planning advice", "Groundwater", "Radon"):
        need(must.replace("m2", "m²") in flat or must.replace("m2", "m 2") in flat, "S9 planning or feasibility caution missing: " + must)
    for bad in ("no planning permission needed", "does not need planning", "always exempt", "guaranteed exempt", "no permission required"):
        need(bad not in low, "S9 blanket exemption wording: " + bad)
    # S10
    for must in ("Advertised prices in each maker’s home market", "No maker has quoted for this page", "checked 8 November 2026",
                 "An Irish installed price isn’t known yet"):
        need(must in flat, "S10 price qualification missing: " + must)
    # S11
    form = re.search(r'<form\b([^>]*)>(.*?)</form>', s, re.S)
    need(len(re.findall(r"<form\b", s)) <= 1, "S11 more than one form")
    if form:
        attrs, fb = form.groups()
        need("action=" not in attrs and 'onsubmit="return false"' in attrs, "S11 the form has an action or can submit")
        need(fb.count("<fieldset disabled>") == 1, "S11 the controls are not inside a disabled fieldset")
        outside = re.sub(r"<fieldset disabled>.*?</fieldset>", "", fb, flags=re.S)
        need(not re.search(r"<(input|select|textarea|button)\b", outside), "S11 a control outside the disabled fieldset")
        need("Preview only." in text(fb) and "nothing typed here would be sent or stored" in text(fb), "S11 the preview notice")
    # The generated site-wide header (pn_header.py, byte-checked by prove-global-header.py) carries PlotNua's general WhatsApp
    # contact pill on every page; it is not a DISC-038 enquiry route, so the scan covers everything outside the header blocks.
    page_only = re.sub(r"<!-- PLOTNUA HEADER v2 · (BAR|ROW) · BEGIN.*?<!-- PLOTNUA HEADER v2 · \1 · END -->", "", s, flags=re.S)
    need(page_only.count("PLOTNUA HEADER v2") == 0 and s.count("PLOTNUA HEADER v2") == 4, "S11 the header blocks are not exactly the generated pair")
    for bad in ("fetch(", "xmlhttprequest", "sendbeacon", "workers.dev", "formspree", "airtable", "wa.me/", "api.whatsapp"):
        need(bad not in page_only.lower(), "S11 data collection or enquiry routing: " + bad)
    # S12
    need("Features are not protection" in flat and "No guarantees" in flat, "S12 the protection cautions")
    for bad in ("guaranteed safe", "bomb-proof", "bombproof", "nuclear-proof", "fully protected", "100% safe", "survive any"):
        need(bad not in low, "S12 unsupported safety claim: " + bad)
    return problems


def main():
    s = read(PAGE)
    files = lambda p: os.path.exists(os.path.join(ROOT, p))
    problems = check(s, files)

    def need(cond, msg):
        if not cond:
            problems.append(msg)

    # S13 containment
    sm, idx, lib = read("sitemap.xml"), read("search-index-v1.json"), read("discoveries.html")
    tm = json.loads(read("atlas-tools/search-topic-map.json"))
    need(PAGE not in sm, "S13 the page is in the sitemap")
    need(PAGE not in idx, "S13 the page is in the search index")
    need(not [e for e in tm["entries"] if PAGE in e.get("targets", [])], "S13 a governed search entry targets the page")
    need(PAGE not in lib, "S13 the Discovery Library links the page")
    # S14 provenance by hash
    reg = json.loads(read("image-provenance-records.json"))
    masters = {r["asset"]: r for r in reg["records"]}
    derivs = {d["asset"]: d for d in reg["derivatives"]}
    used = set(re.findall(r'assets/disc038/img/DISC-038-[A-Za-z0-9-]+\.(?:webp|jpg)', s))
    need(len(used) >= 18, "S14 the DISC-038 images in use (%d)" % len(used))
    sha = lambda a: hashlib.sha256(open(os.path.join(ROOT, a), "rb").read()).hexdigest()
    for a in sorted(used):
        d = derivs.get(a); src = (d or {}).get("derived_from", {}); m = masters.get(src.get("asset"))
        need(d and m and m.get("class") == "AI_ILLUSTRATION", "S14 %s is not a recorded derivative of a declared AI master" % a)
        need(m and "discovery" in m.get("permitted_surfaces", []), "S14 %s: its master does not permit the discovery surface" % a)
        need(d and files(a) and sha(a) == d["sha256"], "S14 %s differs from its recorded derivative" % a)
        need(m and src.get("sha256") == m["sha256"] and sha(m["asset"]) == m["sha256"], "S14 %s: its master is not the declared, unchanged file" % a)
    need("POSSIBLE" in derivs.get("assets/disc038/img/DISC-038-og-1200x630.jpg", {}).get("derived_from", {}).get("asset", ""),
         "S14 the share image is made from the POSSIBLE")

    if "--self-test" in sys.argv:
        faults = {
            "S1": s.replace('<meta name="robots" content="noindex, nofollow">', '<meta name="robots" content="index, follow">', 1),
            "S3": s.replace("<h1>The Hidden Shelter</h1>", "<h1>The Hidden Shelter</h1><h1>x</h1>", 1),
            "S3 ": s.replace('<header class="d-hero ns-hero rg-hero hs-hero', '<div class="pn-hero-compare__mtitle"></div><header class="d-hero ns-hero rg-hero hs-hero', 1),
            "S5": s.replace('id="hsHeroCompare" data-start="100"', 'id="hsHeroCompare" data-start="50"', 1),
            "S5 ": s.replace('<p class="pn-compare__note">%s</p>' % AI, '<p class="pn-compare__note"></p>', 1),
            "S6": s.replace('<p class="lg-kicker">Explore the possibility</p>', '<p class="lg-kicker">Buy now</p>', 1),
            "S7": s.replace('<figure class="hs-section', '<figure class="hs-gone', 1),
            "S8": s.replace("None is a PlotNua partner", "PlotNua is the authorised distributor", 1),
            "S9": s.replace("not for human habitation", "fine for living in", 1),
            "S10": s.replace("No maker has quoted for this page", "Irish price confirmed", 1),
            "S11": s.replace("<fieldset disabled>", "<fieldset>", 1),
            "S11 ": s.replace('onsubmit="return false"', 'action="https://x.workers.dev/submit"', 1),
            "S11  ": s.replace('<ul class="hs-promise"', '<a href="https://wa.me/353000000000?text=HS">WhatsApp us</a><ul class="hs-promise"', 1),
            "S12": s.replace("No guarantees", "Fully protected", 1),
        }
        missed = [k for k, t in faults.items() if not any(p.startswith(k.strip() + " ") for p in check(t, files))]
        print("DISC-038 PAGE · SELF-TEST " + ("OK (%d planted faults caught)" % len(faults) if not missed else "MISSED %s" % missed))
        if missed:
            sys.exit(1)
    if problems:
        print("DISC-038 PAGE · FAILED")
        for p in problems:
            print("  " + p)
        sys.exit(1)
    print("DISC-038 PAGE · OK (S1-S14)")


if __name__ == "__main__":
    main()
