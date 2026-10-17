#!/usr/bin/env python3
"""
GARDEN ROOM PRICES IN IRELAND · BOUNDED BUILDER (SEO Phase 2, founder approval
to build 17 Oct 2026; NOT deployed until the founder approves)
============================================================================
Fills the figure regions of garden-room-prices-ireland.html from PlotNua's
GOVERNED price evidence. Nothing here reads Airtable, and no figure is typed.

  python3 atlas-tools/build-garden-room-prices.py --freeze   (re)write the frozen extract
  python3 atlas-tools/build-garden-room-prices.py            fill the page
  python3 atlas-tools/build-garden-room-prices.py --check    verify, write nothing

THE DATA CHAIN
  atlas-tools/cluster1-cost-evidence.json  -- the frozen evidence behind Living
     in the Garden's "What it costs" section. Its `source.sha256` names the
     exact universe snapshot (research snapshot of 7 October 2026).
  --freeze reads THAT universe snapshot from git history (the revision whose
     bytes hash to source.sha256), classifies every relevant product by what
     its price covers, and REFUSES unless every segment it reproduces matches
     the frozen evidence exactly (count, suppliers, min, median, max, VAT).
     It writes atlas-tools/garden-room-price-page-evidence.json: per product
     only an opaque supplier key, the segment, the euro price, the VAT state
     and the last price-check date. No supplier or product name is stored.
  Build/--check reads that extract, re-proves agreement with the frozen
     evidence, and renders the page regions.

THE RULES (founder, 17 Oct 2026) -- each is a refusal, not a warning
  R1  a range is published only where >= 3 suppliers contribute.
  R2  bases are never combined: one range per segment, no cross-segment figure.
  R3  no average or median is published, and no price per square metre.
  R4  no supplier or product name anywhere on the page.
  R5  freshness: every price inside a published range was checked no more than
      90 days before the build date. A price with NO recorded check date cannot
      show that, so it is left out of the published ranges (counted, never
      hidden). On the first day a published price passes 90 days, --check
      FAILS: the figures must be refreshed (see REFRESH below).
  R6  the page's dataset counts equal the frozen evidence that Living in the
      Garden's own price section is built from, so the two pages can never
      disagree.

REFRESH (when a new research snapshot is approved)
  1. regenerate the universe through the governed refresh;
  2. regenerate cluster1-cost-evidence.json from it (Living in the Garden's
     figures move with it, through its own builder);
  3. run this builder with --freeze, then without flags; commit both files.
"""
import datetime as dt
import hashlib
import html
import json
import pathlib
import re
import statistics
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
EVIDENCE = ROOT / "atlas-tools" / "cluster1-cost-evidence.json"
EXTRACT = ROOT / "atlas-tools" / "garden-room-price-page-evidence.json"
PAGE = ROOT / "garden-room-prices-ireland.html"
UNIVERSE = "garden-room-recommendation-universe-v1.json"
CHECK = "--check" in sys.argv
FREEZE = "--freeze" in sys.argv
MIN_SUPPLIERS = 3
MAX_AGE_DAYS = 90
BUILD_DATE = "2026-10-17"   # the page's dateModified; equals its sitemap lastmod
DESCRIPTION = ("How much does a garden room cost in Ireland? Published price ranges from "
               "PlotNua's research, what the advertised price covers, and how to compare quotes.")
TODAY = dt.date.fromisoformat(
    next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--today=")),
         dt.date.today().isoformat()))

# What each segment means to a homeowner, in the order the page shows them.
# The key is the frozen evidence's own segment name.
SEGMENTS = [
    ("INSTALLED_FINISHED_TURNKEY", "Installed and finished (turnkey)",
     "The supplier's price includes building it on your site and finishing it."),
    ("UNKNOWN_DIY_OR_INSTALLED", "Kit, or installation unclear",
     "The supplier sells it as a kit or installed, and the price does not say which."),
    ("UNKNOWN_NOTHING_PUBLISHED", "What the price covers is not stated",
     "The price is published, but nothing says what it includes."),
    ("SUPPLY_ONLY_INSTALL_SEPARATE", "Supply only, installation extra", ""),
    ("INSTALLED_FINISHED_FOUNDATIONS_EXCLUDED", "Installed, but foundations excluded", ""),
    ("SUPPLIED_AND_ERECTED", "Supplied and erected", ""),
    ("UNKNOWN_DEALER_SOLD", "Sold through a dealer, basis unknown", ""),
]
LABEL = {k: (lab, note) for k, lab, note in SEGMENTS}


def die(msg):
    print("REFUSED: " + msg + " -- nothing written")
    sys.exit(1)


def eur(n):
    return "&euro;{:,}".format(int(round(n)))


def date_long(d):
    return "%d %s %d" % (d.day, d.strftime("%B"), d.year)


# ------------------------------------------------------------------ classify
def relevant(p):
    """Living in the Garden's relevance rule, as recorded in the evidence."""
    return (p.get("currency") == "EUR" and p.get("priceSafeForMatching")
            and not p.get("noPublishedIrishRoute")
            and isinstance(p.get("price"), (int, float))
            and p.get("availabilityStatus") != "Out of Stock")


# The basis lead-phrases that record a foundation exclusion. "BUILDING ONLY,
# THREE EXCLUSIONS" names foundation, electrics and plumbing as excluded.
FOUNDATION_EXCLUDED = re.compile(r"FOUNDATION EXCLUDED|BUILDING ONLY, THREE EXCLUSIONS")


def segment(p):
    lead = (p.get("priceEvidenceRef") or {}).get("basisLeadPhrase")
    im = ((p.get("features") or {}).get("installationModel") or {}).get("text") or ""
    if lead is None and p.get("priceBasisConfidence") == "NO_BASIS_STATED":
        return "UNKNOWN_NOTHING_PUBLISHED"
    if lead == "DIY OR INSTALLED":
        return "UNKNOWN_DIY_OR_INSTALLED"
    if lead == "TURNKEY INSTALLATION INCLUDED":
        return ("INSTALLED_FINISHED_FOUNDATIONS_EXCLUDED" if FOUNDATION_EXCLUDED.search(im)
                else "INSTALLED_FINISHED_TURNKEY")
    if lead == "INSTALLATION AVAILABLE (OPTIONAL)":
        return "SUPPLY_ONLY_INSTALL_SEPARATE"
    if lead == "INSTALLED / ASSEMBLED INCLUDED":
        return "SUPPLIED_AND_ERECTED"
    if lead == "INSTALLATION UNKNOWN":
        return "UNKNOWN_DEALER_SOLD"
    return None


def summarise(rows):
    out = {}
    for key, _, _ in SEGMENTS:
        r = [x for x in rows if x["segment"] == key]
        if not r:
            continue
        prices = [x["price"] for x in r]
        out[key] = {
            "n": len(r), "organisations": len({x["supplierKey"] for x in r}),
            "minEur": min(prices), "medianEur": statistics.median(prices), "maxEur": max(prices),
            "vatIncluded": sum(x["vat"] == "Yes" for x in r),
            "vatExcluded": sum(x["vat"] == "No" for x in r),
            "vatUnknown": sum(x["vat"] not in ("Yes", "No") for x in r),
        }
    return out


def agree(mine, ev, where):
    for key, s in ev["segments"].items():
        m = mine.get(key)
        if not m:
            die("%s: segment %s is in the frozen evidence but not reproduced" % (where, key))
        for f in ("n", "organisations", "minEur", "medianEur", "maxEur",
                  "vatIncluded", "vatExcluded", "vatUnknown"):
            if float(m[f]) != float(s[f]):
                die("%s: %s.%s = %s, frozen evidence says %s" % (where, key, f, m[f], s[f]))
    if set(mine) - set(ev["segments"]):
        die("%s: reproduced segments not in the evidence: %s" % (where, set(mine) - set(ev["segments"])))
    n = sum(m["n"] for m in mine.values())
    if n != ev["totals"]["relevant"]:
        die("%s: %d relevant products, evidence says %d" % (where, n, ev["totals"]["relevant"]))


# -------------------------------------------------------------------- freeze
def freeze(ev):
    want = ev["source"]["sha256"]
    revs = subprocess.run(["git", "log", "--format=%H", "--", UNIVERSE], cwd=ROOT,
                          capture_output=True, text=True).stdout.split()
    snap = None
    for r in revs:
        b = subprocess.run(["git", "show", "%s:%s" % (r, UNIVERSE)], cwd=ROOT,
                           capture_output=True).stdout
        if hashlib.sha256(b).hexdigest() == want:
            snap, rev = json.loads(b), r
            break
    if snap is None:
        die("no revision of %s hashes to the evidence source %s" % (UNIVERSE, want[:12]))
    if snap.get("generated") != ev["source"]["generated"]:
        die("snapshot stamp %s != evidence %s" % (snap.get("generated"), ev["source"]["generated"]))
    rows = []
    for p in snap["products"]:
        if not relevant(p):
            continue
        seg = segment(p)
        if seg is None:
            die("a relevant product has no segment rule: %s" % p.get("id"))
        rows.append({
            "productId": p["id"],
            "supplierKey": hashlib.sha256(p["organisation"].encode()).hexdigest()[:12],
            "segment": seg,
            "price": p["price"],
            "vat": p.get("vatStatus"),
            "lastPriceCheck": (p.get("priceEvidenceRef") or {}).get("lastPriceCheck") or None,
            "priceStatus": (p.get("priceEvidenceRef") or {}).get("status"),
        })
    agree(summarise(rows), ev, "freeze")
    doc = {
        "schema": "plotnua.garden-room-price-page-evidence",
        "version": 1,
        "what_this_is": ("Per-product extract behind garden-room-prices-ireland.html. "
                         "Derived from the universe snapshot named by "
                         "cluster1-cost-evidence.json and proved identical to it, "
                         "segment by segment. Supplier keys are opaque hashes; no "
                         "supplier or product name is stored."),
        "source": {"universe": UNIVERSE, "revision": rev, "sha256": want,
                   "generated": snap["generated"], "evidence": EVIDENCE.name},
        "rows": sorted(rows, key=lambda x: x["productId"]),
    }
    return doc


# --------------------------------------------------------------------- render
def render(ev, ex):
    rows = ex["rows"]
    seg = summarise(rows)
    agree(seg, ev, "build")
    if ex["source"]["sha256"] != ev["source"]["sha256"]:
        die("the extract was frozen from a different snapshot than the evidence")
    snap = dt.date.fromisoformat(ev["source"]["generated"][:10])
    # R5, first half: only prices with a recorded check date can enter a range.
    dated = [r for r in rows if r["lastPriceCheck"]]
    undated = [r for r in rows if not r["lastPriceCheck"]]
    pub_seg = summarise(dated)
    published = [k for k, _, _ in SEGMENTS
                 if k in pub_seg and pub_seg[k]["organisations"] >= MIN_SUPPLIERS]
    held = [k for k, _, _ in SEGMENTS if k in seg and k not in published]
    if published[:1] != ["INSTALLED_FINISHED_TURNKEY"]:
        die("the turnkey segment no longer has %d suppliers; the page's opening answer "
            "is written around it -- re-approve the wording" % MIN_SUPPLIERS)
    # R5 freshness over every price inside a published range
    checks = []
    for r in dated:
        if r["segment"] not in published:
            continue
        d = dt.date.fromisoformat(r["lastPriceCheck"])
        if (TODAY - d).days > MAX_AGE_DAYS:
            die("R5 freshness: a published price was last checked %s, %d days before %s "
                "(limit %d). Refresh the figures." % (d, (TODAY - d).days, TODAY, MAX_AGE_DAYS))
        checks.append(d)
    oldest, newest = min(checks), max(checks)
    expires = oldest + dt.timedelta(days=MAX_AGE_DAYS)

    t = pub_seg["INSTALLED_FINISHED_TURNKEY"]
    regions = {}
    regions["LEAD"] = (
        '<p class="pr-answer">In PlotNua&rsquo;s research, published prices for '
        '<strong>installed, finished garden rooms</strong> ran from '
        '<strong>%s to %s</strong>.</p>\n'
        '<p class="pr-answer-note">That range comes from %d products sold by %d suppliers, '
        'in PlotNua&rsquo;s research snapshot of %s. It is the spread of prices those '
        'suppliers advertise, not a typical Irish price and not an all-in quotation: '
        'foundations, electrical connection and VAT can still sit outside it.</p>'
        % (eur(t["minEur"]), eur(t["maxEur"]), t["n"], t["organisations"], date_long(snap)))

    trs = []
    for k in published:
        s = pub_seg[k]; lab, note = LABEL[k]
        trs.append(
            '      <tr>\n'
            '        <th scope="row"><span class="pr-basis">%s</span><span class="pr-basis-note">%s</span></th>\n'
            '        <td class="pr-range">%s &ndash; %s</td>\n'
            '        <td>%d products<br><span class="pr-sub">%d suppliers</span></td>\n'
            '        <td>%d of %d</td>\n'
            '      </tr>' % (lab, note, eur(s["minEur"]), eur(s["maxEur"]), s["n"],
                             s["organisations"], s["vatIncluded"], s["n"]))
    regions["TABLE"] = (
        '<div class="pr-table-wrap">\n'
        '  <table class="pr-table">\n'
        '    <caption>Published garden room prices in PlotNua&rsquo;s research, grouped by '
        'what the advertised price covers. Research snapshot of %s.</caption>\n'
        '    <thead><tr><th scope="col">What the price covers</th><th scope="col">Published range</th>'
        '<th scope="col">Based on</th><th scope="col">Price says VAT is included</th></tr></thead>\n'
        '    <tbody>\n%s\n    </tbody>\n  </table>\n</div>'
        % (date_long(snap), "\n".join(trs)))

    held_items = "".join('<li>%s: %d product%s from %s supplier%s</li>'
                         % (LABEL[k][0], seg[k]["n"], "" if seg[k]["n"] == 1 else "s",
                            {1: "one", 2: "two"}.get(seg[k]["organisations"], seg[k]["organisations"]),
                            "" if seg[k]["organisations"] == 1 else "s") for k in held)
    regions["HELD"] = (
        '<p class="pr-small">No range is shown where fewer than %d suppliers publish prices '
        'on the same basis, because a range from one or two companies is really their price '
        'list. That applies to:</p>\n<ul class="pr-small-list">%s</ul>' % (MIN_SUPPLIERS, held_items))

    tot = ev["totals"]
    regions["METHOD"] = (
        '<p>These figures come from PlotNua&rsquo;s research snapshot of <strong>%s</strong>: '
        '%d garden room products in the Atlas, of which %d carry a euro price PlotNua can '
        'stand behind, from %d suppliers, with a published route to Irish customers.</p>\n'
        '<p>Every price inside a range above was last checked against the supplier&rsquo;s own '
        'published information between <strong>%s</strong> and <strong>%s</strong>. Ranges are '
        'shown only where at least %d suppliers price on the same basis, and prices on different '
        'bases are never combined.</p>'
        % (date_long(snap), tot["gardenRoomRecords"], tot["relevant"], tot["relevantOrganisations"],
           date_long(oldest), date_long(newest), MIN_SUPPLIERS))
    und_pub = [r for r in undated if r["segment"] in published]
    if und_pub:
        regions["METHOD"] += (
            '\n<p>%d further price%s in these groups %s no recorded check date, so %s left out '
            'of the ranges until %s rechecked.</p>'
            % (len(und_pub), "" if len(und_pub) == 1 else "s",
               "has" if len(und_pub) == 1 else "have", "it is" if len(und_pub) == 1 else "they are",
               "it is" if len(und_pub) == 1 else "they are"))
    regions["ASOF"] = date_long(snap)
    regions["COMPARE"] = (
        '<p>Of the %d priced garden rooms in the research, <strong>%d</strong> do not establish '
        'what the price includes, <strong>%d</strong> do not say whether VAT is in the price, and '
        'only <strong>%d</strong> publish a floor area.</p>'
        % (tot["relevant"], tot["priceBasisNotEstablished"], tot["vatStatusUnknown"],
           tot["floorAreaPublished"]))
    ld = {
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "WebPage", "@id": "https://plotnua.ie/garden-room-prices-ireland.html#webpage",
             "url": "https://plotnua.ie/garden-room-prices-ireland.html",
             "name": "Garden Room Prices in Ireland",
             "description": DESCRIPTION, "inLanguage": "en-IE",
             "dateModified": BUILD_DATE,
             "isPartOf": {"@id": "https://plotnua.ie/#website"},
             "publisher": {"@id": "https://plotnua.ie/#organisation"},
             "breadcrumb": {"@id": "https://plotnua.ie/garden-room-prices-ireland.html#breadcrumb"},
             "mainEntity": {"@id": "https://plotnua.ie/garden-room-prices-ireland.html#dataset"}},
            {"@type": "BreadcrumbList", "@id": "https://plotnua.ie/garden-room-prices-ireland.html#breadcrumb",
             "itemListElement": [
                 {"@type": "ListItem", "position": 1, "name": "PlotNua", "item": "https://plotnua.ie/"},
                 {"@type": "ListItem", "position": 2, "name": "Living in the Garden",
                  "item": "https://plotnua.ie/discovery-living-in-the-garden.html"},
                 {"@type": "ListItem", "position": 3, "name": "Garden Room Prices in Ireland"}]},
            {"@type": "Dataset", "@id": "https://plotnua.ie/garden-room-prices-ireland.html#dataset",
             "name": "Published garden room prices in Ireland, by what the price covers",
             "description": ("Ranges of advertised garden room prices from PlotNua's research "
                             "snapshot of %s, grouped by what each advertised price covers. "
                             "Ranges are shown only where at least %d suppliers price on the "
                             "same basis. Not a census of the Irish market and not a quotation."
                             % (date_long(snap), MIN_SUPPLIERS)),
             "creator": {"@id": "https://plotnua.ie/#organisation"},
             "temporalCoverage": "%s/%s" % (oldest.isoformat(), newest.isoformat()),
             "spatialCoverage": {"@type": "Place", "name": "Ireland"},
             "variableMeasured": "Advertised garden room price in euro, by price basis",
             "isAccessibleForFree": True},
            {"@type": "WebSite", "@id": "https://plotnua.ie/#website", "url": "https://plotnua.ie/",
             "name": "PlotNua", "inLanguage": "en-IE",
             "publisher": {"@id": "https://plotnua.ie/#organisation"}},
            {"@type": "Organization", "@id": "https://plotnua.ie/#organisation",
             "name": "PlotNua", "url": "https://plotnua.ie/"},
        ]}
    regions["JSONLD"] = ('\n<script type="application/ld+json">\n%s\n</script>\n'
                         % json.dumps(ld, indent=2, ensure_ascii=True))

    facts = {"published": {k: pub_seg[k] for k in published}, "held": {k: seg[k] for k in held},
             "excludedNoCheckDate": {k: sum(1 for r in undated if r["segment"] == k)
                                     for k in {r["segment"] for r in undated}},
             "snapshot": snap.isoformat(), "oldestCheck": oldest.isoformat(),
             "newestCheck": newest.isoformat(), "freshUntil": expires.isoformat(),
             "pricesInPublishedRanges": len(checks)}
    return regions, facts


def fill(page, regions):
    out = page
    for k, v in regions.items():
        pat = re.compile(r"(<!-- PN-PRICES:%s -->).*?(<!-- /PN-PRICES:%s -->)" % (k, k), re.S)
        if len(pat.findall(out)) != 1:
            die("page region %s not found exactly once" % k)
        out = pat.sub(lambda m: m.group(1) + v + m.group(2), out)
    return out


def page_guards(text, ex_rows):
    if ('name="description" content="%s"' % DESCRIPTION) not in text:
        die("the meta description is not the one the structured data carries")
    vis = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", " ", text, flags=re.S)
    vis = html.unescape(re.sub(r"<[^>]+>", " ", vis))
    # R3: no average/median, no per-square-metre figure
    if re.search(r"\b(average|median|mean (?:price|cost))\b", vis, re.I):
        bad = re.findall(r".{30}\b(?:average|median)\b.{30}", vis, re.I)
        die("R3 the page states an average/median: %s" % bad[:2])
    if re.search(r"€\s?[\d,]+\s*(?:per|/)\s*(?:m²|m2|sq)", vis, re.I):
        die("R3 the page states a price per square metre")
    # R4: no supplier name. Names come from the CURRENT universe (public data).
    u = json.loads((ROOT / UNIVERSE).read_text(encoding="utf-8"))
    generic = {"Garden Rooms", "Modular House"}   # ordinary words, not identifiers
    names = {p["organisation"] for p in u["products"]} - generic
    hit = sorted(n for n in names if len(n) > 3 and n in vis)
    if hit:
        die("R4 supplier name(s) on the page: %s" % hit[:5])
    # no product imagery
    imgs = re.findall(r"<img\b[^>]*\bsrc=\"([^\"]+)\"", text)
    allowed = {"assets/brand/plotnua-mark-master.svg", "assets/brand/plotnua-icon-transparent.svg"}
    if set(imgs) - allowed:
        die("an image outside the brand marks appears: %s" % sorted(set(imgs) - allowed))


def main():
    ev = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    if FREEZE:
        doc = freeze(ev)
        text = json.dumps(doc, indent=1, ensure_ascii=True) + "\n"
        if CHECK:
            same = EXTRACT.exists() and EXTRACT.read_text(encoding="utf-8") == text
            print("FREEZE CHECK %s" % ("OK" if same else "DIFFERS"))
            sys.exit(0 if same else 1)
        EXTRACT.write_text(text, encoding="utf-8")
        print("  wrote %s (%d products, proved identical to the frozen evidence)"
              % (EXTRACT.name, len(doc["rows"])))
        return
    ex = json.loads(EXTRACT.read_text(encoding="utf-8"))
    regions, facts = render(ev, ex)
    page = PAGE.read_text(encoding="utf-8")
    out = fill(page, regions)
    page_guards(out, ex["rows"])
    print(json.dumps(facts, indent=1))
    if CHECK:
        if out != page:
            die("CHECK: the page's figures are not the ones the evidence produces")
        print("GARDEN ROOM PRICES · CHECK OK — figures agree with the frozen evidence; "
              "fresh until %s" % facts["freshUntil"])
        return
    if out != page:
        PAGE.write_text(out, encoding="utf-8")
        print("  wrote %s" % PAGE.name)
    print("GARDEN ROOM PRICES · built — fresh until %s" % facts["freshUntil"])


if __name__ == "__main__":
    main()
