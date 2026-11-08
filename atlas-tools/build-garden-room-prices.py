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
      Two fixed, figure-free texts may use the word "average" to explain why
      none is published: the NOAVG section and the FAQ_AVG question.
  R4  no supplier or product name anywhere on the page.
  R5  freshness: every price inside a published range was checked no more than
      90 days before the build date. A price with NO recorded check date cannot
      show that, so it is left out of the published ranges (counted, never
      hidden). On the first day a published price passes 90 days, --check
      FAILS: the figures must be refreshed (see REFRESH below).
  R6  the page's dataset counts equal the frozen evidence that Living in the
      Garden's own price section is built from, so the two pages can never
      disagree.
  R7  a segment the founder has held is never published as a range, whatever
      its supplier count (FOUNDER_HELD, below). Releasing one is a founder
      decision, made by removing it from FOUNDER_HELD.

REFRESH (when a new research snapshot is approved)
  1. regenerate the universe through the governed refresh;
  2. regenerate cluster1-cost-evidence.json from it (Living in the Garden's
     figures move with it, through its own builder);
  3. run this builder with --freeze, then without flags; commit both files.
"""
import datetime as dt
import hashlib
import importlib.util
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
# "Substantially higher" means at least this multiple of the published turnkey
# maximum. On the 7 Oct snapshot the highest such price is 3.4x.
SPECIALISED_FACTOR = 1.5
INSTALL_DIFFERS = {"SUPPLY_ONLY_INSTALL_SEPARATE", "INSTALLED_FINISHED_FOUNDATIONS_EXCLUDED",
                   "SUPPLIED_AND_ERECTED", "UNKNOWN_DEALER_SOLD",
                   "INSTALLED_BASE_NOT_STATED"}   # Stage 3D-C2 (7 Nov 2026)
NOAVG_TEXT = (
    '<h2>Why PlotNua does not publish an average garden room price</h2>\n'
    '<p>An average only means something when every price covers the same thing. These do not. '
    'A kit you assemble yourself, a room built and finished on your site, and a price that does '
    'not say what it includes would all count equally, so the result would describe the mix of '
    'products in the research rather than what you would pay.</p>\n'
    '<p>So this guide shows the range for each kind of price, how many products and suppliers '
    'sit behind it, and how many say VAT is included. The same applies to garden offices: they '
    'are priced the same way as garden rooms, and what you pay depends on what is included, not '
    'on what the room is called.</p>')
# FAQ_AVG (founder approval, 19 Oct 2026): the searchers' question "What is the
# average cost of a garden room?" answered by explaining why one average would
# mislead. Like NOAVG it is fixed wording with NO figure, and it is the only other
# place the word "average" may appear (R3). It points to the published ranges and
# to the NOAVG section rather than restating any number next to the word.
FAQ_AVG = (
    "What is the average cost of a garden room?",
    "A single average would mislead you. Advertised garden room prices cover very different "
    "things: a kit you put up yourself, a room built and finished on your site, and a price that "
    "does not say what it includes. Averaging them would describe the mix of products in the "
    "research, not what you would pay. Compare instead within one kind of price: "
    '<a href="#price-ranges">the published ranges</a> show each kind separately, with how many '
    'products and suppliers sit behind it. <a href="#no-average">Why PlotNua does not publish an '
    "average</a> explains this in full.")
FAQ_AVG_HTML = '<div class="pr-faq"><h3>%s</h3>\n<p>%s</p></div>' % FAQ_AVG
# STANDALONE GUIDE PRINCIPLE (governance/STANDALONE-GUIDE-PRINCIPLE.md): the
# guide must show its parent Discovery near the top and invite visitors into
# it further down. Footer links and breadcrumbs do not count.
PARENT_HREF = "discovery-living-in-the-garden.html"
PARENT_TEXT = "Explore Living in the Garden"
PARENT_NAME = "Living in the Garden"
PARENT_MAX_WORDS = 40   # visible words allowed before the parent link
BUILD_DATE = "2026-11-08"   # the page's dateModified; equals its sitemap lastmod
# 8 Nov 2026 (founder SEO-GR3, search relevance and content): presentation and wording only.
# No evidence, range, count, rule, hold or freshness date changes. The meta description now
# names both published ranges and the research totals (DESCRIPTION_FMT); the opening answer
# gives the installed and the kit range side by side, each under its own heading (LEAD); the
# hero line states the research totals, the snapshot date and the check dates (CHECKED); and
# the method section explains how prices are checked, what counts as installed, and VAT
# (METHOD). The snapshot-and-recheck history (ASOF) moves from the hero to the method section.
# 7 Nov 2026 (founder Stage 3D-C2, pricing methodology): "installed and finished" now
# requires published evidence of the building, on-site installation, the required base
# and the standard finish (R-INSTALLED, below); kits are labelled as kits; two new
# founder-held groups (foundations excluded, base not stated); VAT may rest on a
# supplier's current terms of sale (atlas-tools/vat-terms-evidence.json, R-VAT below);
# the "do not establish what the price includes" statistic is retired.
# 6 Nov 2026 (founder decision, staged pricing refresh): 16 base prices rechecked
# (register entry price-recheck-2026-11-06), so the page content changed and its
# dateModified and sitemap lastmod move with it. Stage 2 adds four builder regions:
# CHECKED (visible check dates), VAT, EXTRAS ("What may cost extra", from
# atlas-tools/garden-room-extras-evidence.json, counts only) and the meta description,
# now written from the published figures. The commercial-disclosure guard
# (atlas-tools/check-commercial-disclosure.py) runs on every build and check.
# 20 Oct 2026 (SEO-C1 Release 1): the figures were corrected for five Outdoor Living
# records through atlas-tools/build-cluster1-cost-evidence.py and its register.
# PRICE BY SIZE: NOT PUBLISHED (founder SEO directive, 19 Oct 2026, "price by
# size where evidence supports it"). Tested against the frozen snapshot: only a
# minority of priced rooms publish a floor area, and the Atlas records it on mixed
# bases ("Internal Floor Area" and plain "Floor Area", with incomplete verification
# and scope). A size band would combine measurement bases, which R2 forbids in
# spirit, and only one product passes a strict internal-area test. So the page
# says plainly why there is no price by size (FAQ) instead of publishing one.
# HERO_ILLUSTRATION (founder approval, 23 Oct 2026): the only non-brand images this page may
# show. The hero: PlotNua's own ORIGINAL AI-generated illustration of a generic architectural
# garden pavilion (ChatGPT, supplied by the founder 23 Oct 2026), declared AI_ILLUSTRATION with
# no named product or organisation. It replaced the temporary homepage Possibility Reveal
# illustration, which is no longer permitted here. No identifiable supplier product may appear
# in this generic guide, and no supplier photograph is used here without additional written
# permission.
HERO_ILLUSTRATION = {
    "assets/garden-room-prices/garden-room-prices-hero-2026-10-23-960.avif": "f5ca159b61a95bb129291a693dd1aab37328eadfa076a2b777bb683f5631be7d",
    "assets/garden-room-prices/garden-room-prices-hero-2026-10-23-1672.avif": "d6a86a11293346b51d49386472803160e5d23d937202ebcc0fdb562c13de6edc",
    "assets/garden-room-prices/garden-room-prices-hero-2026-10-23-960.jpg": "a92f40549c52b9f73dfdf9611d9aa1f35e163825a9fc18a8e898c847bc1633ff",
    "assets/garden-room-prices/garden-room-prices-hero-2026-10-23-1672.jpg": "feca00626ff061699a55dd8d1882d74efa0eda57097790f0ce059f4be62ac5b5",
    "assets/garden-room-prices/garden-room-prices-hero-2026-10-23-960.webp": "a016f563d6f422e42c4f212f8fd929cd28523e304c72171c103064ef27ef97fb",
    "assets/garden-room-prices/garden-room-prices-hero-2026-10-23-1672.webp": "e0ca487506f2db412ad00daaa6a60cfec3b01ec4d48e1a2308c30e548c56a531",
}
# The meta description (founder decision, 6 Nov 2026, Stage 2 item 3) is written from
# the published turnkey range, so it can never state a figure the page does not.
# SEO-GR3 (founder, 8 Nov 2026): independent research, installed and kit, multiple suppliers.
# Both figures pairs and both counts come from the same published evidence as the page. The
# kit figure is its published lower bound only, so the first "\u20acX to \u20acY" range on the page stays
# the installed range (prove-matching-eligibility E7 compares it with production).
DESCRIPTION_FMT = ("Independent research on garden room prices in Ireland: %d advertised prices from "
                   "%d suppliers. Installed rooms ran from %s to %s; kits from %s.")
_DESC_CONTEXT = {}   # the kit range and research totals of the last render(), for description(t)


def description(t, kit=None, tot=None):
    # No double quote may appear: the text sits inside a content="..." attribute.
    kit = kit or _DESC_CONTEXT.get("kit")
    tot = tot or _DESC_CONTEXT.get("tot")
    if not kit or not tot:
        die("the meta description needs the published kit range and the research totals")
    e = lambda n: "\u20ac{:,}".format(int(n))
    return DESCRIPTION_FMT % (tot["relevant"], tot["relevantOrganisations"], e(t["minEur"]), e(t["maxEur"]),
                              e(kit["minEur"]))


EXTRAS = ROOT / "atlas-tools" / "garden-room-extras-evidence.json"
EXTRAS_ROWS = (("base", "Base or foundations"), ("delivery", "Delivery"),
               ("electricalConnection", "Electrical connection to the house"))
TODAY = dt.date.fromisoformat(
    next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--today=")),
         dt.date.today().isoformat()))

# What each segment means to a homeowner, in the order the page shows them.
# The key is the frozen evidence's own segment name.
SEGMENTS = [
    # Stage 3D-C2 (founder approval, 7 Nov 2026): the two published groups' labels and notes.
    ("INSTALLED_FINISHED_TURNKEY", "Installed and finished",
     "The supplier's price includes the building, putting it up on your site, the base it "
     "stands on and its standard finish. Delivery, the connection to your house's electricity "
     "and VAT may still need to be confirmed."),
    ("UNKNOWN_DIY_OR_INSTALLED", "Kit or self-build: installation optional or extra",
     "The price is for the building as a kit. Depending on the supplier, assembly, the base, "
     "the electrical connection and other site work may be extra or optional, and delivery "
     "terms differ."),
    ("UNKNOWN_NOTHING_PUBLISHED", "What the price covers is not stated",
     "The price is published, but nothing says what it includes."),
    ("SUPPLY_ONLY_INSTALL_SEPARATE", "Supply only, installation extra", ""),
    ("INSTALLED_FINISHED_FOUNDATIONS_EXCLUDED", "Installed, but foundations excluded", ""),
    ("SUPPLIED_AND_ERECTED", "Supplied and erected", ""),
    ("UNKNOWN_DEALER_SOLD", "Sold through a dealer, basis unknown", ""),
    ("INSTALLED_BASE_NOT_STATED", "Installed, base not stated", ""),
]
LABEL = {k: (lab, note) for k, lab, note in SEGMENTS}

# R7 -- segments held unpublished by founder decision, even at >= MIN_SUPPLIERS.
# Correcting the Outdoor Living installation records moves products into
# "supply only, installation extra"; with the evidence refresh that segment
# could reach 3 suppliers and publish automatically under R1. The founder
# decided it stays unpublished until reviewed.
FOUNDER_HELD = {
    "SUPPLY_ONLY_INSTALL_SEPARATE":
        "Founder direction, 20 Oct 2026: 'Keep the new supply-only price range unpublished.'",
    "INSTALLED_FINISHED_FOUNDATIONS_EXCLUDED":
        "Founder Stage 3D-C2, 7 Nov 2026: Adman reclassified 'Installed, but foundations "
        "excluded'. 'Keep this category founder-held.'",
    "INSTALLED_BASE_NOT_STATED":
        "Founder Stage 3D-C2, 7 Nov 2026: Live in Garden Pods 'Installed, base not stated'. "
        "'Keep this category founder-held.'",
}


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
# Stage 3D-C2 (7 Nov 2026): an installed price whose evidence does not say whether the
# base is included. Read from the classification head only (the text before the first
# full stop), so a later sentence can never move a product into or out of the group.
BASE_NOT_STATED = re.compile(r"FOUNDATION NOT STATED")


def segment(p):
    lead = (p.get("priceEvidenceRef") or {}).get("basisLeadPhrase")
    im = ((p.get("features") or {}).get("installationModel") or {}).get("text") or ""
    if lead is None and p.get("priceBasisConfidence") == "NO_BASIS_STATED":
        return "UNKNOWN_NOTHING_PUBLISHED"
    if lead == "DIY OR INSTALLED":
        return "UNKNOWN_DIY_OR_INSTALLED"
    if lead == "TURNKEY INSTALLATION INCLUDED":
        if BASE_NOT_STATED.search(im.split(".")[0]):
            return "INSTALLED_BASE_NOT_STATED"
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
    # The revision recorded in the existing extract is tried first. Any commit
    # whose tree holds the snapshot is a valid source, but a newest-first search
    # finds a different one depending on clone depth: in a shallow clone the
    # history boundary reports every file as added there (d01758d), while a full
    # clone finds the commit that introduced the snapshot (a3a1b80). Same bytes,
    # same rows; only the recorded revision differed, so --freeze --check failed
    # in CI (fetch-depth 0). The sha256 test below still proves the snapshot.
    if EXTRACT.exists():
        prior = json.loads(EXTRACT.read_text(encoding="utf-8")).get("source", {}).get("revision")
        if prior:
            revs = [prior] + [r for r in revs if r != prior]
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
    # SEO-C1 (20 Oct 2026): the founder-approved record corrections in
    # atlas-tools/cost-evidence-corrections.json, applied by the evidence
    # generator's own function, so the extract and the evidence see the same
    # products. The evidence must name exactly the corrections applied here.
    products, applied = corrections()(snap["products"])
    if [c["id"] for c in applied] != [c["id"] for c in ev.get("corrections") or []]:
        die("the evidence and the corrections register disagree on which corrections apply")
    rows = []
    for p in products:
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
            # Stage 3D-C2: carried only where the VAT position rests on supplier terms.
            **({"vatBasis": (p.get("priceEvidence") or {})["vatBasis"]}
               if (p.get("priceEvidence") or {}).get("vatBasis") else {}),
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
                   "generated": snap["generated"], "evidence": EVIDENCE.name,
                   **({"corrections": [{"id": c["id"], "deployedCommit": c["deployedCommit"],
                                        "products": [x["id"] for x in c["products"]]} for c in applied]}
                      if applied else {})},
        "rows": sorted(rows, key=lambda x: x["productId"]),
    }
    return doc


def corrections():
    """apply(products) -> (products, applied), from the evidence generator."""
    spec = importlib.util.spec_from_file_location(
        "cluster1_cost_evidence", ROOT / "atlas-tools" / "build-cluster1-cost-evidence.py")
    g = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(g)
    reg = g.register()
    return lambda products: g.apply_corrections(products, reg)


def as_of(ev, snap):
    """The snapshot date, with the approved note for any applied correction
    (SEO-C1 decision D2): '7 October 2026, corrected on 20 October 2026 for
    five supplier records'."""
    notes = [c["pageNote"] for c in ev.get("corrections") or []]
    return date_long(snap) + "".join(", " + n for n in notes)


# The founder-approved explanation that replaces the retired statistic (Stage 3D-C2,
# 7 Nov 2026). Fixed words, no figure; the same words on Living in the Garden.
COMPARE_EXPLANATION = (
    "Not every garden-room price covers the same things. Some prices include the building, "
    "foundations and installation. Others are for kits or buildings that need additional work. "
    "PlotNua separates these so you can compare your options more confidently.")
RETIRED_STATISTIC = re.compile(r"do(?:es)? not establish what the price includes", re.I)

# ------------------------------------------------------- R-VAT (Stage 3D-C2)
VAT_REGISTER = ROOT / "atlas-tools" / "vat-terms-evidence.json"
VAT_FOOTNOTE = (
    "PlotNua counts a price as including VAT where the supplier says so beside the price or, "
    "for all its website prices, in its current terms of sale. PlotNua records what suppliers "
    "state; it does not check or confirm any supplier&rsquo;s VAT rate or tax treatment. Ask "
    "for the VAT-inclusive total in writing.")


def vat_register():
    """Founder rule B with safeguards (Stage 3D-C2, 7 Nov 2026). A VAT position resting on
    a supplier's terms of sale is counted only while its register entry is current."""
    doc = json.loads(VAT_REGISTER.read_text(encoding="utf-8"))
    if doc.get("schema") != "plotnua.vat-terms-evidence":
        die("R-VAT the VAT terms register has the wrong schema")
    return doc


def vat_guards(rows):
    """R-VAT. Every row whose VAT position rests on supplier terms must be covered by an
    ACCEPTED register entry for its supplier that is current (checked within MAX_AGE_DAYS),
    names the product among the pages checked with no contrary wording, and passed the
    rate-consistency safeguard. A product the register accepts must carry the basis (so a
    regenerated record cannot silently turn a terms-based position into a price-level one),
    and no supplier the register does NOT rely on may contribute a terms-based position."""
    doc = vat_register()
    acc = {}
    for e in doc["suppliers"]:
        key = hashlib.sha256(e["organisation"].encode()).hexdigest()[:12]
        if e["status"] == "accepted":
            for f in ("quote", "clause", "source", "checked", "coversWebsitePrices", "productPagesChecked",
                      "contraryWordingFound", "rateCheck", "expires"):
                if f not in e or e[f] in (None, "", []):
                    die("R-VAT %s: the accepted entry has no %s" % (e["organisation"], f))
            d = dt.date.fromisoformat(e["checked"])
            if dt.date.fromisoformat(e["expires"]) != d + dt.timedelta(days=MAX_AGE_DAYS):
                die("R-VAT %s: expiry must be %d days after the check" % (e["organisation"], MAX_AGE_DAYS))
            if (TODAY - d).days > MAX_AGE_DAYS:
                die("R-VAT %s: the terms were last read %s, more than %d days ago; re-read them or "
                    "stop counting these prices as VAT-inclusive" % (e["organisation"], d, MAX_AGE_DAYS))
            if e["coversWebsitePrices"] is not True or e["contraryWordingFound"] is not False \
                    or e["rateCheck"].get("result") != "consistent":
                die("R-VAT %s: the terms do not cover website prices, a page contradicts them, or "
                    "the rate-consistency safeguard failed" % e["organisation"])
            acc[key] = (e, {x["productId"] for x in e["productPagesChecked"]})
        elif e["status"] != "not-relied-on":
            die("R-VAT %s: unknown status %r" % (e["organisation"], e["status"]))
    for r in rows:
        basis = r.get("vatBasis")
        if basis not in (None, "supplier-terms"):
            die("R-VAT %s: unknown VAT basis %r" % (r["productId"], basis))
        if basis == "supplier-terms":
            if r["vat"] != "Yes" or r["supplierKey"] not in acc or r["productId"] not in acc[r["supplierKey"]][1]:
                die("R-VAT %s: a terms-based VAT position without a current accepted register entry "
                    "naming this product" % r["productId"])
        elif r["supplierKey"] in acc and r["productId"] in acc[r["supplierKey"]][1]:
            die("R-VAT %s: the register accepts this product's terms-based VAT position but the "
                "record does not carry it" % r["productId"])
    return doc


# --------------------------------------------------------------------- render
def render(ev, ex):
    rows = ex["rows"]
    seg = summarise(rows)
    agree(seg, ev, "build")
    vat_guards(rows)
    if ex["source"]["sha256"] != ev["source"]["sha256"]:
        die("the extract was frozen from a different snapshot than the evidence")
    if [c["id"] for c in ex["source"].get("corrections") or []] != \
            [c["id"] for c in ev.get("corrections") or []]:
        die("the extract and the evidence carry different corrections")
    snap = dt.date.fromisoformat(ev["source"]["generated"][:10])
    # R5, first half: only prices with a recorded check date can enter a range.
    dated = [r for r in rows if r["lastPriceCheck"]]
    undated = [r for r in rows if not r["lastPriceCheck"]]
    pub_seg = summarise(dated)
    published = [k for k, _, _ in SEGMENTS
                 if k in pub_seg and pub_seg[k]["organisations"] >= MIN_SUPPLIERS
                 and k not in FOUNDER_HELD]
    if set(published) & set(FOUNDER_HELD):
        die("R7 a founder-held segment would be published: %s" % sorted(set(published) & set(FOUNDER_HELD)))
    held = [k for k, _, _ in SEGMENTS if k in seg and k not in published]
    # A founder-held segment that has reached MIN_SUPPLIERS is held by decision,
    # not by the supplier count, so it must not be listed under the R1 sentence.
    by_decision = [k for k in held if k in FOUNDER_HELD and k in pub_seg
                   and pub_seg[k]["organisations"] >= MIN_SUPPLIERS]
    held = [k for k in held if k not in by_decision]
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
    kit = pub_seg.get("UNKNOWN_DIY_OR_INSTALLED")
    if not kit or "UNKNOWN_DIY_OR_INSTALLED" not in published:
        die("the kit or self-build range is no longer published -- the opening answer, the meta "
            "description and the FAQ are written around it; re-approve the wording")
    tot = ev["totals"]
    _DESC_CONTEXT.clear(); _DESC_CONTEXT.update(kit=kit, tot=tot)
    regions = {}
    # SEO-GR3 (founder, 8 Nov 2026): both published ranges side by side, each under its own
    # heading, with what each kind of price covers and how many products and suppliers sit
    # behind it. The ranges are the observed spread in PlotNua's research, so the note says
    # they are neither typical prices nor the limits of the Irish market.
    card = ('<div class="pr-range-card">\n'
            '<h3>%s</h3>\n'
            '<p class="pr-range-fig">%s &ndash; %s</p>\n'
            '<p>%s %d products from %d suppliers.</p>\n'
            '</div>')
    regions["LEAD"] = (
        '<p class="pr-answer">In PlotNua&rsquo;s research, garden room prices come in two '
        'very different kinds: a room <strong>installed and finished</strong> on your site, '
        'or a <strong>kit</strong> that you or a builder put up.</p>\n'
        '<div class="pr-ranges">\n%s\n%s\n</div>\n'
        '<p class="pr-answer-note">Each range runs from the lowest to the highest price advertised '
        'in that group of PlotNua&rsquo;s research. It is not a typical Irish price, and not the '
        'lowest or highest price on the Irish market. Neither is an all-in quotation: delivery, the '
        'connection to your house&rsquo;s electricity and VAT can sit outside an installed price, '
        'and a kit price leaves putting the building up to you or a builder you hire.</p>'
        % (card % ("Installed garden room costs", eur(t["minEur"]), eur(t["maxEur"]),
                   "Installed and finished: the building, putting it up on your site, the base it "
                   "stands on and its standard finish.", t["n"], t["organisations"]),
           card % ("Garden room kit prices", eur(kit["minEur"]), eur(kit["maxEur"]),
                   "Kit or self-build: installation is optional or extra, and the base and the "
                   "electrical connection may be extra too.", kit["n"], kit["organisations"])))
    # Stage 2 item 6 (6 Nov 2026): straight from the answer to the products. No name and no
    # count (R4, R6); not "the products behind this range", because the Discovery lists
    # only what PlotNua currently publishes.
    regions["LEAD"] += (
        '\n<p class="pr-small pr-makers-link">See the garden rooms PlotNua publishes, with '
        'their makers, specifications and prices. <a href="%s#explore-makers">Explore garden '
        'rooms and makers&nbsp;&rarr;</a></p>' % PARENT_HREF)
    # Stage 2 item 1: the check dates, visible near the top of the page. SEO-GR3: with the
    # research totals and the snapshot date, so the first screen says what the figures are.
    # The snapshot date and the check dates stay separate statements: the prices were not
    # all rechecked on one day.
    regions["CHECKED"] = (
        '<p class="pr-asof">Independent research: %d priced garden room products from %d suppliers, '
        'in PlotNua&rsquo;s research snapshot of %s. The %d prices in the published ranges were '
        'each last checked against the supplier&rsquo;s own published information between %s and %s. '
        '<a href="#how-these-figures-were-made">How the evidence is checked</a></p>'
        % (tot["relevant"], tot["relevantOrganisations"], date_long(snap), len(checks),
           date_long(oldest), date_long(newest)))
    # Stage 2 item 4: VAT, from the same rows as the range.
    regions["VAT"] = (
        '<h3 class="pd-h3">VAT in these prices</h3>\n'
        '<p class="pr-small">Of the %d installed, finished prices in the range above, %d %s VAT '
        'is included, %d %s it is not, and %d %s not say. A price shown &ldquo;+VAT&rdquo; or '
        '&ldquo;ex VAT&rdquo; is less than you will pay, so add VAT before comparing it with a '
        'VAT-inclusive price, and ask every supplier for the VAT-inclusive total in writing.</p>'
        % (t["n"], t["vatIncluded"], "says" if t["vatIncluded"] == 1 else "say",
           t["vatExcluded"], "says" if t["vatExcluded"] == 1 else "say",
           t["vatUnknown"], "does" if t["vatUnknown"] == 1 else "do"))
    regions["EXTRAS"] = extras(dated, t)
    regions["_DESC"] = description(t)

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
        '<th scope="col">Based on</th><th scope="col">VAT included, as stated by the supplier</th></tr></thead>\n'
        '    <tbody>\n%s\n    </tbody>\n  </table>\n</div>\n'
        # Stage 3D-C2 (founder approval, 7 Nov 2026): the VAT footnote, beneath the table.
        '<p class="pr-small pr-vat-note">%s</p>\n'
        # SEO-C2.2 (20 Oct 2026): from the prices to the makers behind them, with
        # no name on this page (R4). No count, so it cannot disagree with R6.
        # Not "every maker behind these prices": two suppliers in the 7 Oct
        # snapshot are held from publication today (Cosy Cabins, Premium Log House).
        '<p class="pr-small pr-makers-link">Living in the Garden lists every garden room maker '
        'PlotNua currently publishes. <a href="%s#maker-index">Browse the makers, A to Z&nbsp;&rarr;</a></p>'
        % (date_long(snap), "\n".join(trs), VAT_FOOTNOTE, PARENT_HREF))

    held_items = "".join('<li>%s: %d product%s from %s supplier%s</li>'
                         % (LABEL[k][0], seg[k]["n"], "" if seg[k]["n"] == 1 else "s",
                            {1: "one", 2: "two"}.get(seg[k]["organisations"], seg[k]["organisations"]),
                            "" if seg[k]["organisations"] == 1 else "s") for k in held)
    regions["HELD"] = (
        '<p class="pr-small">No range is shown where fewer than %d suppliers publish prices '
        'on the same basis, because a range from one or two companies is really their price '
        'list. That applies to:</p>\n<ul class="pr-small-list">%s</ul>' % (MIN_SUPPLIERS, held_items))
    if by_decision:
        # WORDING NOT YET APPROVED: this branch is first reached at an evidence
        # refresh, and the founder reviews the page before that refresh ships.
        regions["HELD"] += (
            '\n<p class="pr-small">PlotNua is also not yet showing a range for these, while it '
            'confirms with suppliers what the advertised prices include:</p>\n'
            '<ul class="pr-small-list">%s</ul>'
            % "".join('<li>%s: %d products from %d suppliers</li>'
                      % (LABEL[k][0], seg[k]["n"], seg[k]["organisations"]) for k in by_decision))

    # SEO-GR3 (founder, 8 Nov 2026): the method, under plain sub-headings, adds how freshness and
    # withdrawals work, what counts as installed (R-INSTALLED) and how VAT is recorded (R-VAT).
    # Every figure is the builder's own; the two original paragraphs are unchanged.
    regions["METHOD"] = (
        '<h3>What the research covers</h3>\n'
        '<p>These figures come from PlotNua&rsquo;s research snapshot of <strong>%s</strong>: '
        '%d garden room products in the Atlas, of which %d carry a euro price PlotNua can '
        'stand behind, from %d suppliers, with a published route to Irish customers.</p>\n'
        '<h3>How each price is checked</h3>\n'
        '<p>Every price inside a range above was last checked against the supplier&rsquo;s own '
        'published information between <strong>%s</strong> and <strong>%s</strong>. Ranges are '
        'shown only where at least %d suppliers price on the same basis, and prices on different '
        'bases are never combined.</p>\n'
        '<p>A price stays in a published range only while its last check is no more than %d days '
        'old: PlotNua&rsquo;s daily check fails as soon as one is older, and the range must then be '
        'rechecked. A price PlotNua cannot currently verify is withdrawn rather than estimated, and '
        'no figure is added that a supplier does not publish.</p>\n'
        '<h3>Installed or kit</h3>\n'
        '<p>A price counts as installed and finished only where the supplier&rsquo;s published '
        'information covers the building, putting it up on your site, the base it stands on and its '
        'standard finish. A kit is counted as a kit. Prices on any other basis, or whose basis is not '
        'stated, are counted separately and never mixed into these ranges.</p>\n'
        '<h3>VAT</h3>\n'
        '<p>PlotNua records the VAT position each supplier states, beside the price or in its current '
        'terms of sale, and does not check any supplier&rsquo;s VAT rate or tax treatment. Where a '
        'price does not say, PlotNua counts it as not stated rather than assuming either way.</p>'
        % (date_long(snap), tot["gardenRoomRecords"], tot["relevant"], tot["relevantOrganisations"],
           date_long(oldest), date_long(newest), MIN_SUPPLIERS, MAX_AGE_DAYS))
    und_pub = [r for r in undated if r["segment"] in published]
    if und_pub:
        regions["METHOD"] += (
            '\n<p>%d further price%s in these groups %s no recorded check date, so %s left out '
            'of the ranges until %s rechecked.</p>'
            % (len(und_pub), "" if len(und_pub) == 1 else "s",
               "has" if len(und_pub) == 1 else "have", "it is" if len(und_pub) == 1 else "they are",
               "it is" if len(und_pub) == 1 else "they are"))
    regions["ASOF"] = as_of(ev, snap)
    # SEO guide phase 1 (17 Oct 2026): the disclosure research made prominent.
    # Same three figures, same source, now set as figures rather than a sentence.
    # Stage 3D-C2 (founder decision, 7 Nov 2026): the statistic "N of 237 published prices
    # do not establish what the price includes" is RETIRED (it counted every kit) and is not
    # replaced by another count. The approved explanation takes its place; the detailed
    # category counts stay in the table and the held-group list above.
    regions["COMPARE"] = (
        '<p class="pr-stats-intro">%s</p>\n'
        '<div class="pr-stats">\n'
        '  <p class="pr-stat"><span class="pr-stat-n">%d</span><span class="pr-stat-l">of %d '
        'do not say whether VAT is in the price</span></p>\n'
        '  <p class="pr-stat"><span class="pr-stat-n">%d</span><span class="pr-stat-l">of %d '
        'publish a floor area</span></p>\n'
        '</div>\n'
        '<p class="pr-stats-src">PlotNua&rsquo;s research snapshot of %s: every priced garden '
        'room in the research, %d in all.</p>'
        % (COMPARE_EXPLANATION, tot["vatStatusUnknown"], tot["relevant"],
           tot["floorAreaPublished"], tot["relevant"], date_long(snap), tot["relevant"]))

    # FAQ (19 Oct 2026): short answers to the questions searchers ask, built
    # only from the figures above and the page's own approved wording.
    a3 = ('PlotNua cannot give an honest price for one size. Only %d of the %d priced garden '
          'rooms in its research publish a floor area at all, and suppliers measure it in '
          'different ways, inside or out, so a price for a 3 &times; 3&nbsp;m room would rest on '
          'too few figures that do not compare. Ask each supplier for the internal floor area and '
          'the price for the same finish.' % (tot["floorAreaPublished"], tot["relevant"]))
    kit = pub_seg.get("UNKNOWN_DIY_OR_INSTALLED")
    if not kit:
        die("FAQ: the kit or self-build range is no longer published -- re-approve the wording")
    faq = [
        FAQ_AVG,
        ("How much does a 3 &times; 3&nbsp;m garden room cost?",
         a3 + ' <a href="#quote-checklist">The quote checklist</a> covers both.'),
        ("Is it cheaper to buy a kit than an installed garden room?",
         'Kit prices start lower, but a kit buys less. In PlotNua&rsquo;s research, prices for '
         'a kit or self-build, where installation is optional or extra, ran from %s to %s, and '
         'installed, finished rooms from %s to %s. A kit price leaves putting the building up to '
         'you or a builder you hire, and usually leaves out the base and the electrical '
         'connection, so price those before comparing. '
         '<a href="#quote-checklist">The quote checklist</a> shows what to ask.'
         % (eur(kit["minEur"]), eur(kit["maxEur"]), eur(t["minEur"]), eur(t["maxEur"]))),
        ("Do garden room prices include VAT?",
         'Often the price does not say. Of the %d installed, finished prices in the range above, '
         '%d say VAT is included, and across all %d priced garden rooms in PlotNua&rsquo;s research, '
         '%d do not say either way. Ask for the VAT position in writing.'
         % (t["n"], t["vatIncluded"], tot["relevant"], tot["vatStatusUnknown"])),
        ("What else should I budget for besides the room itself?",
         'Foundations and groundwork, delivery, installation, the electrical connection and VAT can '
         'all sit outside an advertised price. <a href="#outside-the-price">See what can sit outside '
         'the advertised price</a>.'),
        ("Do I need planning permission for a garden room?",
         'It depends on the room&rsquo;s size, height, position and use, and on your garden. '
         '<a href="discovery-living-in-the-garden.html">Living in the Garden</a> explains the 2026 '
         'exemption conditions and when the Building Regulations apply.'),
    ]
    regions["FAQ"] = "\n".join('<div class="pr-faq"><h3>%s</h3>\n<p>%s</p></div>' % qa for qa in faq)
    regions["UPDATED"] = date_long(dt.date.fromisoformat(BUILD_DATE))

    # SPECIALISED (founder wording, 17 Oct 2026), emitted only while the evidence
    # makes every clause of it true:
    #   "substantially higher": at least one relevant price is >= SPECIALISED_FACTOR
    #     x the published turnkey maximum;
    #   "not included in the comparison above": every such price sits in a group
    #     that has NO published range (so it is in neither the opening range nor
    #     the table);
    #   "pricing and installation arrangements differ": every such group is one
    #     whose basis differs on installation (supply only, foundations excluded,
    #     supplied and erected, dealer-sold).
    # If any clause stops holding, the build refuses and the wording returns to
    # the founder. No figure, name or count is published by this sentence.
    high = [r for r in rows if r["price"] >= SPECIALISED_FACTOR * t["maxEur"]]
    if not high:
        die("SPECIALISED: no price is substantially above the turnkey range any more; "
            "the sentence would be untrue -- re-approve the wording")
    if any(r["segment"] in published for r in high):
        die("SPECIALISED: a substantially higher price now sits inside a published range; "
            "'not included in the comparison above' would be untrue -- re-approve the wording")
    if any(r["segment"] not in INSTALL_DIFFERS for r in high):
        die("SPECIALISED: a substantially higher price is in a group whose installation "
            "basis is not different -- re-approve the wording")
    regions["SPECIALISED"] = (
        '<p class="pr-specialised">Some specialised garden buildings in PlotNua&rsquo;s research '
        'are advertised at substantially higher prices. These are not included in the comparison '
        'above because their pricing and installation arrangements differ.</p>')

    # NOAVG (founder approval, 17 Oct 2026): why there is no average. Fixed
    # words, no figures; the only place the word "average" may appear (R3).
    regions["NOAVG"] = NOAVG_TEXT
    ld = {
        "@context": "https://schema.org",
        "@graph": [
            {"@type": "WebPage", "@id": "https://plotnua.ie/garden-room-prices-ireland.html#webpage",
             "url": "https://plotnua.ie/garden-room-prices-ireland.html",
             "name": "Garden Room Prices in Ireland",
             "description": regions["_DESC"], "inLanguage": "en-IE",
             "dateModified": BUILD_DATE,
             # about (19 Oct 2026): what the page is about, as plain named things. No
             # FAQPage, Dataset or Product markup: see the notes below and the
             # Search Console decision of 18 Oct 2026.
             "about": [{"@type": "Thing", "name": "Garden room prices in Ireland"},
                       {"@type": "Thing", "name": "Garden offices"}],
             "isPartOf": {"@id": "https://plotnua.ie/#website"},
             "publisher": {"@id": "https://plotnua.ie/#organisation"},
             "breadcrumb": {"@id": "https://plotnua.ie/garden-room-prices-ireland.html#breadcrumb"}},
            {"@type": "BreadcrumbList", "@id": "https://plotnua.ie/garden-room-prices-ireland.html#breadcrumb",
             "itemListElement": [
                 {"@type": "ListItem", "position": 1, "name": "PlotNua", "item": "https://plotnua.ie/"},
                 {"@type": "ListItem", "position": 2, "name": "Living in the Garden",
                  "item": "https://plotnua.ie/discovery-living-in-the-garden.html"},
                 {"@type": "ListItem", "position": 3, "name": "Garden Room Prices in Ireland"}]},
            # No Dataset node (Search Console, 18 Oct 2026): the visible table is a summary
            # of PlotNua's proprietary research, not a distributed dataset, and its terms
            # do not permit reuse. WebPage and BreadcrumbList describe the page.
            {"@type": "WebSite", "@id": "https://plotnua.ie/#website", "url": "https://plotnua.ie/",
             "name": "PlotNua", "inLanguage": "en-IE",
             "publisher": {"@id": "https://plotnua.ie/#organisation"}},
            {"@type": "Organization", "@id": "https://plotnua.ie/#organisation",
             "name": "PlotNua", "url": "https://plotnua.ie/"},
        ]}
    regions["JSONLD"] = ('\n<script type="application/ld+json">\n%s\n</script>\n'
                         % json.dumps(ld, indent=2, ensure_ascii=True))

    facts = {"published": {k: pub_seg[k] for k in published}, "held": {k: seg[k] for k in held},
             "heldByFounderDecision": {k: seg[k] for k in by_decision},
             "excludedNoCheckDate": {k: sum(1 for r in undated if r["segment"] == k)
                                     for k in {r["segment"] for r in undated}},
             "snapshot": snap.isoformat(), "oldestCheck": oldest.isoformat(),
             "newestCheck": newest.isoformat(), "freshUntil": expires.isoformat(),
             "pricesInPublishedRanges": len(checks)}
    return regions, facts


def extras(dated, t):
    """Stage 2 item 5: what the suppliers behind the published turnkey range say about
    three costs. Counts only. Refuses unless the evidence covers exactly those suppliers,
    every state is known, and every statement was checked within MAX_AGE_DAYS (R5)."""
    doc = json.loads(EXTRAS.read_text(encoding="utf-8"))
    want = {r["supplierKey"] for r in dated if r["segment"] == "INSTALLED_FINISHED_TURNKEY"}
    sup = doc["suppliers"]
    have = [hashlib.sha256(x["organisation"].encode()).hexdigest()[:12] for x in sup]
    if len(have) != len(set(have)) or set(have) != want or len(want) != t["organisations"]:
        die("EXTRAS the evidence does not cover exactly the %d suppliers in the published "
            "installed range" % t["organisations"])
    # R-INSTALLED (Stage 3D-C2, founder approval 7 Nov 2026): a supplier's price is
    # "installed and finished" only where published evidence establishes the building,
    # on-site installation, the required base and the standard finish. The classification
    # establishes installation and finish; the base must be shown INCLUDED, and current,
    # for every supplier in the published range, or the build refuses.
    for x in sup:
        b = x.get("base") or {}
        if b.get("state") != "included":
            die("R-INSTALLED %s is in the published installed-and-finished range but its base is "
                "%r, not established as included" % (x["organisation"], b.get("state")))
    dates = []
    counts = {}
    for k, _ in EXTRAS_ROWS:
        c = {"included": 0, "extra": 0, "notEstablished": 0}
        for x in sup:
            e = x.get(k) or {}
            if e.get("state") not in c or not e.get("evidence") or not e.get("source"):
                die("EXTRAS %s: %s has no recognised state, evidence and source" % (k, x["organisation"]))
            d = dt.date.fromisoformat(e["checked"])
            if (TODAY - d).days > MAX_AGE_DAYS:
                die("EXTRAS %s: %s was checked %s, more than %d days ago" % (k, x["organisation"], d, MAX_AGE_DAYS))
            c[e["state"]] += 1
            dates.append(d)
        counts[k] = c
    word = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine"}
    n = t["organisations"]

    # Stage 3D-C2: a state no supplier is in is left out rather than counted as "by 0", and a
    # state every supplier is in reads "by all four".
    def parts(c):
        out = []
        for k, phrase in (("included", "included in the price by"),
                          ("extra", "charged separately or left to you by"),
                          ("notEstablished", "not stated by")):
            if c[k]:
                out.append("%s %s%s" % (phrase, "all " if c[k] == n and n > 1 else "", word.get(c[k], c[k])))
        return ", ".join(out)
    items = "".join('<li><strong>%s:</strong> %s.</li>' % (label, parts(counts[k])) for k, label in EXTRAS_ROWS)
    return (
        '<h3 class="pd-h3" id="what-may-cost-extra">What may cost extra: what the %s suppliers behind the installed range say</h3>\n'
        '<p>The installed, finished range above comes from %s suppliers. This is what they publish '
        'about three costs that often sit outside the advertised price. PlotNua shows how many say '
        'each thing, not who.</p>\n'
        '<ul class="pr-small-list">%s</ul>\n'
        '<p class="pr-small">Checked against each supplier&rsquo;s published information between %s '
        'and %s. &ldquo;Not stated&rdquo; means PlotNua holds no published statement either way, so '
        'ask. <a href="#quote-checklist">The quote checklist</a> covers all three.</p>'
        % (word.get(n, n), word.get(n, n), items, date_long(min(dates)), date_long(max(dates))))


def fill(page, regions):
    out = page
    desc = regions.get("_DESC")
    if desc is not None:
        pat = re.compile(r'(<meta name="description" content=")[^"]*(">)')
        if len(pat.findall(out)) != 1:
            die("the meta description tag is not found exactly once")
        out = pat.sub(lambda m: m.group(1) + html.escape(desc, quote=False) + m.group(2), out)
    for k, v in regions.items():
        if k.startswith("_"):
            continue
        pat = re.compile(r"(<!-- PN-PRICES:%s -->).*?(<!-- /PN-PRICES:%s -->)" % (k, k), re.S)
        if len(pat.findall(out)) != 1:
            die("page region %s not found exactly once" % k)
        out = pat.sub(lambda m: m.group(1) + v + m.group(2), out)
    return out


def parent_guards(text):
    """G-PARENT: the standalone guide principle. Refuses a page whose parent
    Discovery is only reachable through the footer or breadcrumbs."""
    hero = re.search(r'<header class="pr-hero">(.*?)</header>', text, re.S)
    if not hero:
        die("G-PARENT the guide hero is missing")
    link = re.search(r'<a class="pr-parent" href="%s">([^<]*)</a>' % re.escape(PARENT_HREF), hero.group(1))
    if not link or PARENT_TEXT not in html.unescape(link.group(1)):
        die("G-PARENT the hero has no visible '%s' link to %s" % (PARENT_TEXT, PARENT_HREF))
    before = re.sub(r"<[^>]+>", " ", hero.group(1)[:link.start()])
    if len(before.split()) > PARENT_MAX_WORDS:
        die("G-PARENT the parent link is not near the top of the guide")
    css = " ".join(re.findall(r"\.pr-parent[^{]*\{([^}]*)\}", text))
    if re.search(r"display\s*:\s*none|visibility\s*:\s*hidden|opacity\s*:\s*0(?![.\d])", css):
        die("G-PARENT the parent link is hidden by CSS")
    hero_txt = html.unescape(re.sub(r"<[^>]+>", " ", hero.group(1)))
    if not re.search(r"Part of\s+%s" % re.escape(PARENT_NAME), hero_txt):
        die("G-PARENT the hero does not say the guide is part of %s" % PARENT_NAME)
    inv = re.search(r'<section[^>]*id="explore-the-discovery"[^>]*>(.*?)</section>', text, re.S)
    if not inv:
        die("G-PARENT the invitation to explore the Discovery is missing")
    for need in ('href="%s"' % PARENT_HREF, 'href="%s#explore-makers"' % PARENT_HREF):
        if need not in inv.group(1):
            die("G-PARENT the invitation does not link %s" % need)


def page_guards(text, ex_rows, desc):
    if ('name="description" content="%s"' % html.escape(desc, quote=False)) not in text:
        die("the meta description is not the one the structured data carries")
    if re.search(r"&euro;|€", re.sub(r"<[^>]+>", " ", re.search(
            r"<!-- PN-PRICES:EXTRAS -->(.*?)<!-- /PN-PRICES:EXTRAS -->", text, re.S).group(1))):
        die("EXTRAS the extra-costs section states a euro amount")
    # R3 exemption, scoped: the NOAVG region is fixed text that explains why no
    # average is published. It must carry no figure at all; everything outside
    # it is still held to the full rule.
    m = re.search(r"<!-- PN-PRICES:NOAVG -->(.*?)<!-- /PN-PRICES:NOAVG -->", text, re.S)
    if not m or m.group(1) != NOAVG_TEXT:
        die("R3 the no-average explanation is missing or not the approved text")
    if re.search(r"\d|&euro;|€", re.sub(r"<[^>]+>", " ", m.group(1))):
        die("R3 the no-average explanation contains a figure")
    text_r3 = text.replace(m.group(0), " ")
    # The FAQ_AVG question: present exactly once, inside the FAQ region, exactly the
    # approved words, with no figure. Then it too is set aside for the R3 scan.
    faq_m = re.search(r"<!-- PN-PRICES:FAQ -->(.*?)<!-- /PN-PRICES:FAQ -->", text, re.S)
    if not faq_m or faq_m.group(1).count(FAQ_AVG_HTML) != 1 or text.count(FAQ_AVG_HTML) != 1:
        die("R3 the average-cost question is missing or not the approved text")
    if re.search(r"\d|&euro;|€", re.sub(r"<[^>]+>", " ", FAQ_AVG_HTML)):
        die("R3 the average-cost question contains a figure")
    text_r3 = text_r3.replace(FAQ_AVG_HTML, " ")
    vis = re.sub(r"<script.*?</script>|<style.*?</style>|<!--.*?-->", " ", text_r3, flags=re.S)
    vis = html.unescape(re.sub(r"<[^>]+>", " ", vis))
    parent_guards(text)
    # Stage 3D-C2: the retired statistic is gone and the approved explanation is in place.
    if RETIRED_STATISTIC.search(vis):
        die("the retired 'do not establish what the price includes' statistic is on the page")
    if COMPARE_EXPLANATION not in vis:
        die("the approved price explanation is missing from the page")
    if html.unescape(VAT_FOOTNOTE) not in vis:
        die("R-VAT the VAT footnote is missing from the page")
    # R7: no founder-held segment appears in the published table
    tbl = re.search(r"<!-- PN-PRICES:TABLE -->(.*?)<!-- /PN-PRICES:TABLE -->", text, re.S)
    if not tbl:
        die("the price table region is missing")
    for k in FOUNDER_HELD:
        if LABEL[k][0] in html.unescape(tbl.group(1)):
            die("R7 the founder-held segment '%s' appears in the price table" % LABEL[k][0])
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
    # R4, extended (SEO-C2.2): no supplier or product name in any link text or
    # title attribute either, including links that lead to the makers.
    pnames = {p["productName"] for p in u["products"] if p.get("productName")}
    labels = [html.unescape(re.sub(r"<[^>]+>", " ", t)) for t in re.findall(r"<a\b[^>]*>(.*?)</a>", text, re.S)]
    labels += [html.unescape(t) for t in re.findall(r'\btitle="([^"]*)"', text)]
    lab_hit = sorted({n for n in (names | pnames) if len(n) > 3 for l in labels if n in l})
    if lab_hit:
        die("R4 supplier or product name in a link or title: %s" % lab_hit[:5])
    if 'href="%s#maker-index"' % PARENT_HREF not in text:
        die("C2.2 the link from the prices to the maker index is missing")
    # no product imagery. ONE exception (founder approval, 23 Oct 2026): the guide
    # hero may show PlotNua's own original garden-pavilion illustration, exactly the files
    # pinned in HERO_ILLUSTRATION, only inside the hero, only with its visible
    # "AI-generated illustration" label, and only while each file's provenance record is an
    # AI illustration of no named product or organisation that may appear on a Discovery
    # surface. Anything else is still refused.
    imgs = re.findall(r"<img\b[^>]*\bsrc=\"([^\"]+)\"", text)
    allowed = {"assets/brand/plotnua-mark-master.svg", "assets/brand/plotnua-icon-transparent.svg",
               "/assets/brand/plotart-p-48.webp"}   # the PlotArt logo in the shared header (31 Oct 2026)
    hero = re.search(r'<header class="pr-hero">(.*?)</header>', text, re.S).group(1)
    srcs = set(re.findall(r"<img\b[^>]*\bsrc=\"([^\"]+)\"", hero))
    srcs |= {u.split()[0] for ss in re.findall(r'\bsrcset="([^"]+)"', hero) for u in ss.split(",")}
    rest = text.replace(hero, " ", 1)                       # everything except the hero
    outside = [i for i in re.findall(r"<img\b[^>]*\bsrc=\"([^\"]+)\"", rest) if i not in allowed]
    if outside or (srcs - allowed - set(HERO_ILLUSTRATION)):
        die("an image outside the brand marks appears: %s" % sorted(set(outside) | (srcs - allowed - set(HERO_ILLUSTRATION))))
    used = srcs & set(HERO_ILLUSTRATION)
    if used:
        if "AI-generated illustration" not in html.unescape(re.sub(r"<[^>]+>", " ", hero)):
            die("HERO the illustration is not labelled 'AI-generated illustration'")
        prov = json.loads((ROOT / "image-provenance-records.json").read_text(encoding="utf-8"))
        recs = {r["asset"]: r for r in prov["records"]}
        for f in sorted(used):
            if hashlib.sha256((ROOT / f).read_bytes()).hexdigest() != HERO_ILLUSTRATION[f]:
                die("HERO %s is not the pinned file" % f)
            r = recs.get(f)
            if not r or r.get("class") != "AI_ILLUSTRATION" or r.get("depicts_named_product") is not False \
                    or r.get("depicts_named_organisation") is not False or "discovery" not in (r.get("permitted_surfaces") or []):
                die("HERO %s: its provenance record does not permit it here" % f)


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
    page_guards(out, ex["rows"], regions["_DESC"])
    spec = importlib.util.spec_from_file_location("commercial_disclosure",
                                                  ROOT / "atlas-tools" / "check-commercial-disclosure.py")
    cd = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(cd)
    reg, _, _, litg = cd.load()
    for b in cd.problems(reg, ex, out, litg):
        die("COMMERCIAL " + b)
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
