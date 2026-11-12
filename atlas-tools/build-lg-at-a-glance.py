#!/usr/bin/env python3
"""PLOTNUA · DISC-008 Living in the Garden: "Garden rooms in Ireland, compared." (SEO-GRR, rev. 2, 12 Nov 2026).

A short, early answer for the search intent "garden rooms Ireland", placed after the hero and before
chapter 01. It adds no new facts.

  R1  Rows: EVERY published, indexable supplier profile (suppliers/*.html in the sitemap) whose maker
      has garden rooms in the page's Maker Explorer. Every other published profile must be declared in
      NOT_GARDEN_ROOM_PROFILES with its reason, so a new profile cannot be silently left out or added.
      Listed A to Z. Never ranked, never "recommended".
  R2  Figures: the explorer's own garden-room tab figures (published products, makers, confirmed for
      Ireland) and, per maker, its garden rooms in the explorer.
  R3  Prices: no figure is shown. Each maker's explorer price labels are summarised by kind, with the
      explorer's own meanings (build-maker-explorer.py): a recorded price that fails the price checks
      or whose freshness date has passed is "not currently verified"; no usable price is "no
      published price"; a quote-only record is "priced on enquiry". A freshness date ("fu") that has
      passed is applied here exactly as maker-explorer.js applies it. An unknown label refuses.
      A maker-level wording override (PRICE_EVIDENCE) is allowed only where the maker's own profile
      and its showcase evidence say so, and only while the explorer label is compatible with it.
  R4  Images: only an image already used on this page or the maker's profile, with its required
      credit; visualisations labelled. Makers without a suitable garden-room photograph, or whose
      listing preview is pending, are text-only.
  R5  Links: the maker's profile; the explorer and the prices guide both above and below the rows;
      the garden-offices guide and the existing planning chapter below. No new planning statement.
  R6  Disclosure: "no agreed commercial arrangement" — refused if any listed maker is on the ACTIVE
      commercial-arrangements register (check-commercial-disclosure.py covers the same makers).
  R7  The DISC-008 content guard declaration ("atAGlance") is written from the same output, and the
      guard (run by the Image rights gate) refuses a page whose block no longer matches the data.

  python3 atlas-tools/build-lg-at-a-glance.py            write the block and the declaration
  python3 atlas-tools/build-lg-at-a-glance.py --check    exit 1 if either is stale
"""
import datetime, hashlib, html, json, os, re, sys
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PAGE = os.path.join(ROOT, "discovery-living-in-the-garden.html")
ADDED = os.path.join(ROOT, "atlas-tools", "premium-discovery", "living-garden-added.json")
REGISTER = os.path.join(ROOT, "atlas-tools", "commercial-arrangements-register.json")
SITEMAP = os.path.join(ROOT, "sitemap.xml")
BEGIN = "<!-- PN-LG-AT-A-GLANCE v1 · BEGIN · built by atlas-tools/build-lg-at-a-glance.py from #mx-data — do not hand-edit -->"
END = "<!-- PN-LG-AT-A-GLANCE v1 · END -->"
ANCHOR = '<div class="lg-chapter" id="lg-ch01">'
SNAPSHOT = "7 October 2026"   # the research snapshot the explorer is built from (chapter 04 states it, with its corrections)

# R1: profile -> explorer maker. "says" is the row's description; every "pin" must appear on the profile.
MAKERS = [
    {"explorer": "Don Modular Homes", "name": "Don Modular Homes", "profile": "suppliers/don-modular-homes.html",
     "says": "One steel-framed, factory-finished design, from a 25 m² garden room to a four-bedroom home.",
     "pin": ["steel-framed, factory-finished design", "25 m² garden room to a four-bedroom home"],
     "img": {"src": "https://donmodularhomes.ie/images/don-modular-home-exterior.webp",
             "alt": "Visualisation: dark-clad modular home at dusk with a glazed gable end, in a woodland clearing",
             "kind": "Visualisation", "credit": "© Don Modular Homes", "credit_href": None}},
    {"explorer": "Elm Landscaping (Garden Rooms)", "name": "Elm Landscaping", "profile": "suppliers/elm-landscaping.html",
     "says": "A Co. Clare landscaping company that also supplies timber garden rooms and log cabins.",
     "pin": ["a Co. Clare landscaping company, also supplies timber garden rooms and log cabins"],
     "img": None},  # Elm's permitted imagery is landscaping, not garden rooms (R4)
    {"explorer": "Garden Room Ireland", "name": "Garden Room Ireland", "profile": "suppliers/garden-room-ireland.html",
     "says": "Insulated steel-clad garden rooms, built in Dublin.",
     "pin": ["insulated steel-clad garden rooms in Dublin"],
     "img": {"src": "https://static.wixstatic.com/media/fef4b6_f1486b2ae80e4ed2bfeecde2d7e5ea71~mv2.jpg",
             "alt": "Timber-clad garden room under a mature tree, with a stepping-stone path",
             "kind": "Photograph", "credit": "© Garden Room Ireland", "credit_href": None}},
    {"explorer": "Gardenhouse24 Ireland", "name": "Gardenhouse24", "profile": "suppliers/gardenhouse24.html",
     "says": "Nordic-spruce garden rooms and log cabins, sold as kits; foundation, insulation, electrics and installation are priced separately.",
     "pin": ["Nordic-spruce garden rooms, log cabins", "Each one starts as a kit, and the foundation, roof covering, insulation, electrics and installation are chosen and priced separately"],
     "img": {"src": "https://d1l23c7hiawhq3.cloudfront.net/media/catalog/product/cache/631d00a18cc6f2d63e06f2111d31fb8f/2/0/20220606161922_img_0390_1.jpg",
             "alt": "A natural-timber ALU CONCEPT 44 A garden room with full-height aluminium sliding glazing on two sides",
             "kind": "Photograph", "credit": "Image: Gardenhouse24", "credit_href": "https://gardenhouse24.ie/"}},
    {"explorer": "NOOK Prefab (espacio NOOK)", "name": "NOOK Prefab", "profile": "suppliers/nook-prefab.html",
     "says": "NOOK 10 and NOOK 20 garden rooms, made in Spain and delivered finished.",
     "pin": ["NOOK 10 and NOOK 20 garden rooms, made in Spain and delivered finished"],
     "img": None},  # founder, 12 Nov 2026: text-only in this revision (NOOK asked to preview listings)
    {"explorer": "The Pod Factory", "name": "The Pod Factory", "profile": "suppliers/the-pod-factory.html",
     "says": "Steel-framed garden studios and garden pods, built in Co. Meath and craned into place.",
     "pin": ["steel-framed garden studios, garden pods", "built in Co. Meath and craned into place"],
     "img": {"src": "https://www.thepodfactory.ie/wp-content/uploads/2023/05/Showroom-Pod-17-scaled.jpg",
             "alt": "A single-storey garden pod with cedar cladding, a dark grey render frame and full-height anthracite glazing",
             "kind": "Photograph", "credit": "Image: The Pod Factory", "credit_href": "https://www.thepodfactory.ie/"}},
]
# R1: published profiles that are not garden-room makers in the explorer, with the reason.
NOT_GARDEN_ROOM_PROFILES = {
    "suppliers/the-mobile-pods.html": "no garden rooms in the Maker Explorer (its pods are not listed there)",
    "suppliers/superior-pergola-ireland.html": "pergolas and verandas, not garden rooms",
    "suppliers/arctic-wellness.html": "saunas and cold-water immersion, not garden rooms",
    "suppliers/invitation.html": "supplier-facing page, noindex",
}
# R3: maker-level wording from authoritative evidence. Applies only while every explorer label for the
# maker is one of "allowed"; otherwise the build refuses so the wording is reviewed.
PRICE_EVIDENCE = {
    "The Pod Factory": {
        "text": "No published price; each pod is priced on enquiry.",
        "allowed": {"unavailable", "enquiry"},
        "profile_pin": ["Price on enquiry"],
        "evidence_file": "supplier-preview-system/showcases/the-pod-factory/showcase.json",
        "evidence_pin": ["No price list is published", "the supplier prices each one for the client; ask for a quote"],
    },
}

PRICE_KINDS = [
    ("hold", re.compile(r"^(Not currently taking orders|Out of stock|Price requires verification)")),
    ("unverified", re.compile(r"^Price not currently verified$")),
    ("unavailable", re.compile(r"^Price unavailable$")),
    ("enquiry", re.compile(r"^Price on (enquiry|request)$")),
    ("gbp", re.compile(r"£")),
    ("eur_exworks", re.compile(r"€.*excluding VAT.*Ex works", re.I | re.S)),
    ("eur_excl", re.compile(r"€.*excl", re.I)),
    ("eur_incl", re.compile(r"€.*incl", re.I)),
    ("eur_nostated", re.compile(r"€.*VAT not stated")),
]
KIND_TEXT = {
    "eur_incl": "euro price shown, including VAT",
    "eur_nostated": "euro price shown; VAT not stated",
    "eur_excl": "euro price shown, excluding VAT",
    # NOOK founder rule (6 Nov 2026): its qualification travels with any mention of its price.
    "eur_exworks": "starting price shown. Ex works. VAT, delivery, foundations and installation are additional. Irish delivery terms require confirmation",
    "gbp": "UK sterling price shown",
    "enquiry": "priced on enquiry",
    "unverified": "published price not currently verified, so not shown",
    "unavailable": "no published price",
    "hold": "not currently available to order",
}
ORDER = ["eur_incl", "eur_nostated", "eur_excl", "eur_exworks", "gbp", "enquiry", "unverified", "unavailable", "hold"]
AVAIL = {"c": "Confirmed", "u": "Not yet confirmed", "r": "No published Irish route"}


def refuse(msg):
    sys.exit("REFUSED: " + msg)


def esc(s):
    return html.escape(s, quote=True)


def explorer_tab(src):
    m = re.search(r'<script type="application/json" class="pn-mx-config" id="mx-data">(.*?)</script>', src, re.S)
    if not m:
        refuse("the Maker Explorer data (#mx-data) is missing")
    return next(t for t in json.loads(m.group(1))["tabs"] if t["key"] == "gardenRooms")


def kind_of(prod, today):
    lab = prod[4] if len(prod) > 4 else ""
    nav = prod[5] if len(prod) > 5 and isinstance(prod[5], dict) else {}
    if nav.get("fu") and nav["fu"] < today:      # the explorer's own expiry, applied at build time
        return "unverified"
    for k, rx in PRICE_KINDS:
        if rx.search(lab):
            return k
    refuse("R3 unknown explorer price label %r" % lab)


def price_summary(kinds):
    c, n = Counter(kinds), len(kinds)
    parts = []
    for k in ORDER:
        if not c[k]:
            continue
        t = KIND_TEXT[k]
        t = t[0].upper() + t[1:]
        parts.append(t if n == 1 else "%s (%s)" % (t, ("all %d" % n) if c[k] == n else "%d of %d" % (c[k], n)))
    return "; ".join(parts) + "."


def avail_summary(codes):
    c = Counter(codes)
    if len(c) == 1:
        return AVAIL[codes[0]]
    return "; ".join("%s for %d" % (AVAIL[k], v) for k, v in c.items())


def published_profiles():
    sm = open(SITEMAP, encoding="utf-8").read()
    return sorted(set(re.findall(r"<loc>https://plotnua\.ie/(suppliers/[^<]+\.html)</loc>", sm)))


def build(src, today=None):
    today = today or datetime.date.today().isoformat()
    tab = explorer_tab(src)
    fig = tab["figures"]
    makers = {m["m"]: m for m in tab["makers"]}
    # R1: every published profile is either a row or a declared exclusion
    rows_for = {mk["profile"] for mk in MAKERS}
    for p in published_profiles():
        if p not in rows_for and p not in NOT_GARDEN_ROOM_PROFILES:
            refuse("R1 published profile %s is neither a row nor a declared exclusion" % p)
    register = json.load(open(REGISTER, encoding="utf-8"))
    active = {a["key"] for a in register.get("active", [])}
    rows, credits = [], []
    for mk in MAKERS:
        prof = os.path.join(ROOT, mk["profile"])
        if not os.path.exists(prof):
            refuse("R1 profile missing: " + mk["profile"])
        ps = html.unescape(open(prof, encoding="utf-8").read())
        if '<meta name="robots" content="index, follow"' not in ps:
            refuse("R1 profile is not indexable: " + mk["profile"])
        for p in mk["pin"]:
            if p not in ps:
                refuse("R1 %s no longer says %r" % (mk["profile"], p))
        if mk["explorer"] not in makers or not makers[mk["explorer"]]["p"]:
            refuse("R1 %s has no garden rooms in the explorer" % mk["explorer"])
        if hashlib.sha256(mk["explorer"].encode()).hexdigest()[:12] in active:
            refuse("R6 %s holds an ACTIVE commercial arrangement: the disclosure would be false" % mk["explorer"])
        prods = makers[mk["explorer"]]["p"]
        kinds = [kind_of(p, today) for p in prods]
        ev = PRICE_EVIDENCE.get(mk["name"])
        if ev:
            if not set(kinds) <= ev["allowed"]:
                refuse("R3 %s: explorer labels %s no longer fit the evidence wording; review it" % (mk["name"], sorted(set(kinds))))
            for p in ev["profile_pin"]:
                if p not in ps: refuse("R3 %s profile no longer says %r" % (mk["name"], p))
            evs = open(os.path.join(ROOT, ev["evidence_file"]), encoding="utf-8").read()
            for p in ev["evidence_pin"]:
                if p not in evs: refuse("R3 %s evidence no longer says %r" % (mk["name"], p))
            price = ev["text"]
        else:
            price = price_summary(kinds)
        img = mk["img"]
        if img:
            if img["src"] not in ps and img["src"] not in src:
                refuse("R4 image is not already used on this page or the profile: " + img["src"])
            fig_html = ('<span class="lg-glance-thumb"><img class="lg-glance-img" src="%s" alt="%s" width="56" height="42" '
                        'loading="lazy" decoding="async">%s</span>'
                        % (esc(img["src"]), esc(img["alt"]),
                           '<span class="lg-glance-kind">Visualisation</span>' if img["kind"] == "Visualisation" else ""))
            c = esc(img["credit"])
            credits.append('<a href="%s" target="_blank" rel="noopener noreferrer">%s</a>' % (esc(img["credit_href"]), c)
                           if img["credit_href"] else c)
        else:
            fig_html = ""
        n = len(prods)
        rows.append(
            '        <tr><th scope="row"><span class="lg-glance-maker">%s<a href="%s">%s</a></span></th>\n'
            '          <td class="lg-g-what">%s</td>\n'
            '          <td class="lg-g-n" data-l="Garden rooms">%d</td>\n'
            '          <td class="lg-g-ie" data-l="In Ireland">%s</td>\n'
            '          <td class="lg-g-price" data-l="Prices">%s</td></tr>' % (
                fig_html, esc(mk["profile"]), esc(mk["name"]), esc(mk["says"]), n,
                esc(avail_summary([p[3] for p in prods])), esc(price)))
    total = "{:,}".format(fig["products"])
    lead = ("PlotNua lists %s garden rooms from %d makers; %s are confirmed as available in Ireland. "
            "These are the makers with a full PlotNua profile." % (total, fig["makers"], "{:,}".format(fig["confirmed"])))
    return """%s
<section class="lg-glance" id="garden-rooms-at-a-glance" aria-labelledby="lg-glance-h">
  <style>
    .lg-glance{margin:0 0 72px;padding:0 0 44px;border-bottom:1px solid rgba(242,235,224,.14)}
    .lg-glance a{color:inherit;text-decoration:underline;text-decoration-color:rgba(143,175,138,.6);text-underline-offset:4px}
    .lg-glance a:hover,.lg-glance a:focus-visible{text-decoration-color:currentColor}
    .lg-glance-top{display:flex;flex-wrap:wrap;gap:6px 26px;margin:20px 0 0;font-size:15px}
    .lg-glance .gr-compare{min-width:760px}
    .lg-glance .gr-compare th,.lg-glance .gr-compare td{padding:12px 14px}
    .lg-glance .gr-compare tbody th{width:24%%}
    .lg-glance-maker{display:flex;align-items:center;gap:12px}
    .lg-glance-thumb{flex:0 0 56px;width:56px}
    .lg-glance-img{display:block;width:56px;height:42px;object-fit:cover;border-radius:2px}
    .lg-glance-kind{display:block;font-size:10px;letter-spacing:.04em;opacity:.7;margin-top:2px;font-weight:400}
    .lg-glance .lg-route-links{margin-top:22px}
    @media (max-width:640px){
      .lg-glance{margin-bottom:56px;padding-bottom:32px}
      .lg-glance .gr-compare-wrap{overflow:visible;margin-top:16px}
      .lg-glance .gr-compare,.lg-glance .gr-compare tbody,.lg-glance .gr-compare caption{display:block;width:auto;min-width:0}
      .lg-glance .gr-compare caption{font-size:12px;padding-bottom:6px}
      .lg-glance .gr-compare thead{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0)}
      .lg-glance .gr-compare tr{display:flex;flex-wrap:wrap;gap:2px 18px;padding:14px 0;border-bottom:1px solid rgba(242,235,224,.14)}
      .lg-glance .gr-compare th,.lg-glance .gr-compare td{display:block;border:0;padding:0;font-size:14px;line-height:1.5}
      .lg-glance .gr-compare tbody th,.lg-glance .gr-compare td.lg-g-what,.lg-glance .gr-compare td.lg-g-price{flex:0 0 100%%;width:auto}
      .lg-glance .gr-compare tbody th{margin-bottom:4px}
      .lg-glance .gr-compare td.lg-g-what{opacity:.85;margin-bottom:4px}
      .lg-glance .gr-compare td[data-l]::before{content:attr(data-l) ": ";font-weight:600;opacity:.75}
      .lg-glance-thumb{flex-basis:48px;width:48px}
      .lg-glance-img{width:48px;height:36px}
    }
  </style>
  <p class="lg-kicker">At a glance</p>
  <h2 class="lg-title" id="lg-glance-h">Garden rooms in Ireland, compared.</h2>
  <p class="lg-stand">%s</p>
  <p class="lg-glance-top"><a href="#suppliers">Browse all %s in the Maker Explorer</a><a href="garden-room-prices-ireland.html">Compare published prices</a></p>
  <div class="gr-compare-wrap" role="region" aria-label="Garden room makers compared; scroll horizontally on small screens" tabindex="0">
    <table class="gr-compare">
      <caption>All %d makers with a published PlotNua profile and garden rooms in the Maker Explorer, A to Z. Not a ranking: PlotNua has no agreed commercial arrangement with any maker listed here. Counts are the garden rooms PlotNua publishes, from its %s research snapshot as corrected since.</caption>
      <thead><tr><th scope="col">Maker</th><th scope="col">What they make</th><th scope="col">Garden rooms</th><th scope="col">In Ireland</th><th scope="col">Prices on PlotNua</th></tr></thead>
      <tbody>
%s
      </tbody>
    </table>
  </div>
  <p class="pd-small" style="margin-top:12px">Images: %s. Shown as supplied by each maker; a visualisation is computer-generated, not a photograph.</p>
  <ul class="lg-route-links" role="list">
    <li><a href="#suppliers">Every maker and all %s garden rooms</a></li>
    <li><a href="garden-room-prices-ireland.html">Compare published prices: garden room prices in Ireland</a></li>
    <li><a href="garden-offices-ireland.html">Working from home: garden offices in Ireland</a></li>
    <li><a href="#planning-conditions">What the 2026 planning conditions say</a></li>
  </ul>
</section>
%s
""" % (BEGIN, lead, total, len(MAKERS), SNAPSHOT, "\n".join(rows), "; ".join(credits), total, END)


def guard_parser():
    import importlib.util
    spec = importlib.util.spec_from_file_location("lg_guard", os.path.join(ROOT, "atlas-tools", "prove-premium-discovery-living-garden.py"))
    g = importlib.util.module_from_spec(spec); spec.loader.exec_module(g)
    return g.Blocks()


def declaration(block):
    p = guard_parser(); p.feed(block); p.close()
    return {"declared": "2026-11-12, SEO-GRR rev. 2 (garden rooms Ireland visibility): an early comparison after the "
                        "hero, built by atlas-tools/build-lg-at-a-glance.py from the page's Maker Explorer data. "
                        "Founder approval required before release.",
            "blocks": p.out, "links": p.links, "imgs": p.imgs, "ids": p.ids}


def current_block(src):
    if BEGIN not in src:
        return None
    a = src.index(BEGIN); z = src.index(END) + len(END) + 1
    return src[a:z]


def splice(src, block):
    if BEGIN in src:
        a = src.index(BEGIN); z = src.index(END) + len(END) + 1
        return src[:a] + block + src[z:]
    i = src.index(ANCHOR)
    return src[:i] + block + src[i:]


def main():
    check = "--check" in sys.argv
    src = open(PAGE, encoding="utf-8").read()
    block = build(src)
    new = splice(src, block)
    added = json.load(open(ADDED, encoding="utf-8"))
    want = declaration(block)
    if check:
        bad = []
        if new != src: bad.append("the block on the page is stale or missing")
        if added.get("atAGlance") != [want]: bad.append("the DISC-008 guard declaration (atAGlance) is stale or missing")
        if bad:
            print("AT A GLANCE · STALE: " + "; ".join(bad)); sys.exit(1)
        print("AT A GLANCE · OK — block and guard declaration match the Maker Explorer data, the %d profiles and the "
              "commercial-arrangements register" % len(MAKERS))
        return
    added["atAGlance"] = [want]
    open(PAGE, "w", encoding="utf-8").write(new)
    open(ADDED, "w", encoding="utf-8").write(json.dumps(added, ensure_ascii=False, indent=1) + "\n")
    print("AT A GLANCE · WROTE block (%d makers) and the atAGlance declaration" % len(MAKERS))


if __name__ == "__main__":
    main()
