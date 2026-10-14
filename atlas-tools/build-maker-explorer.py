#!/usr/bin/env python3
"""
PLOTNUA MAKER EXPLORER — BOUNDED BUILDER · v2, REUSABLE COMPONENT (13 Oct 2026)

HISTORY
  v1 (13 Oct 2026) built the explorer into Living in the Garden with its
  JavaScript and CSS inline. Founder decisions that day: concept approved,
  twelve refinements, "The Scannal" display name, top "Show fewer makers",
  compact reset, and the TRIQ QUBE box removed (product name corrected 13 Oct 2026).
  v2 (13 Oct 2026, founder: "Reusable component · Phase 2") extracts ONE
  shared implementation and drives it from per-Discovery configuration,
  without changing appearance, behaviour or eligibility.

THE COMPONENT
  maker-explorer.js   one implementation, reads only its page's config
  maker-explorer.css  one stylesheet, scoped to section#explore-makers
  Both are PINNED here by sha256 (guard G11): a change to either is a
  deliberate re-pin, never a drift.

PER-DISCOVERY CONFIGURATION (PAGES below)
  copy, tabs (label, nouns, published SOURCE, product navigation), headline
  figures, placement anchors. A page gets the explorer ONLY by being listed
  in PAGES. Today that is Living in the Garden alone.

SOURCES ARE PUBLISHED ELIGIBILITY FILES, NEVER ATLAS
  A tab can name only a source in SOURCES. Each source is a published,
  already-governed universe in this repository, read with its OWN
  eligibility rule; nothing here reads Airtable or re-decides eligibility.
    garden-room-universe-v1      every product is eligible (header-checked)
    additional-home-universe-v1  qualification.state == ELIGIBLE only
  A source declares whether its products have a PlotNua product page. Only
  then may a tab link products (your-plot.html?product={id}); otherwise the
  tab must carry a route to the existing journey where they are shown.

GUARDS (G1-G11), unchanged in strictness from v1, now per tab
  G1 counts == universe headers · G2 no held/excluded product; listed == the
  eligible set · G3 no external link; product links only where the source
  allows · G4 no storage/fetch/analytics/URL state · G5 A-Z directory, the
  initial order a shuffle · G6 no endorsement vocabulary · G7 no special
  supplier placement; TRIQ stays published and in Search · G8 no area figure
  in page prose · G9 nothing outside the block (and the stylesheet link)
  changes; placement · G10 no research note in a displayed name · G11 shared
  files pinned, host tokens present, exactly one link and one script.

  python3 atlas-tools/build-maker-explorer.py --check | --apply   (all PAGES)
"""
import ast, hashlib, html, json, pathlib, re, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SEARCH_BUILDER = ROOT / "atlas-tools" / "build-search-index.py"
MARK = "PLOTNUA-MAKER-EXPLORER-V1"
V1_CSS_MARK = "PLOTNUA MAKER EXPLORER v1"          # the inline block v1 wrote
SHARED_JS, SHARED_CSS = "maker-explorer.js", "maker-explorer.css"
PINS = {
    # Re-pinned 14 Oct 2026: the summary line now says "1 maker" / "1 product"
    # rather than "1 makers", and the "Show all" control is hidden when every
    # maker already fits (Garden Retreat lists one maker). Output for any
    # directory larger than six makers is unchanged, so Living in the Garden
    # is identical.
    # Re-pinned 14 Oct 2026 (Garden Retreat restructure): optional per-tab
    # availabilityNote and an optional price line per product. A tab without
    # either renders exactly as before (Living in the Garden is unchanged;
    # proved by an output comparison before and after the re-pin).
    # Previous pin: 76846752dc52234d91aee875ed4e5afd0d409f41e1d52fd87474cccebcba3358
    # Re-pinned 14 Oct 2026 (Garden Retreat pre-launch corrections): optional
    # per-product navigation proved by the builder (maker's own page where the
    # grant includes a link back; enumerated authorised images with label and
    # credit), and one read of the URL fragment (#p-<product id>) to open a
    # listed product. Living in the Garden carries none of it and is unchanged.
    # Previous pin: 983a253b77d400033d9c45b324adec17e7c0c8f27b6b2f530c392bc13c6ecb39
    SHARED_JS:  "11335fd6f56cdb9bcc2aca96a36b9b432d4e83eff7d931d03b47a41924ddc984",
    # Re-pinned 13 Oct 2026: the stylesheet is now shared with the Provider
    # Explorer (The Borrowed Garden). Every rule is scoped to
    # :is(#explore-makers, #explore-providers), which keeps each rule's
    # specificity identical; Living in the Garden is pixel-identical (10-state
    # parity capture). Previous pin:
    # 30d1c90403c73cdf71794c916515b70415997b85737dad8b48178acd540443ee
    SHARED_CSS: "d571b8ca399ce2653231f9293aeb261eed2eaf909196b446edb473b5a781c2c7",
}
CSS_LINK = '<link rel="stylesheet" href="maker-explorer.css">'
JS_TAG = '<script src="maker-explorer.js"></script>'
HOST_TOKENS = ("--paper", "--cream", "--ink", "--soft", "--accent", "--oak")

def die(m): print("REFUSED: " + m); sys.exit(2)

# ── naming (unchanged from v1) ───────────────────────────────────────────────
# The organisation Atlas records literally as "Garden Rooms" (ORG-000001)
# reads as a category; its own Atlas Website field is gardenrooms.ie.
DISPLAY_ALIAS = {"Garden Rooms": "Garden Rooms (gardenrooms.ie)"}

# Presentation only, never written back to Atlas; each entry pins the exact
# Atlas name it corrects and refuses if Atlas changes.
DISPLAY_NAME_BY_ID = {
    "recKFWluu0vDEHn81": {
        "atlas": "The Scannal (3-Bedroom Cabin, listed under Two Bed)",
        "display": "The Scannal",
        "evidence": "All In One Cabins two-bed-cabins page, read 13 Oct 2026: the "
                    "product heading is 'The scannal' (navigation tab 'The Scannal'). "
                    "The parenthesis is PlotNua's note of a taxonomy conflict (the "
                    "supplier's copy says '3 bedroom' on its 'Two Bed Cabins' page), "
                    "recorded in the Atlas description. Display uses the supplier's "
                    "own heading only; no bedroom count is asserted.",
    },
}
ANNOTATION_RE = re.compile(r"listed under|unresolved|conflict|taxonomy|vendor|placeholder|"
                           r"\bTBC\b|\bTBD\b|\bunknown\b|\?|\bsee note|\bper atlas", re.I)
BANNED = ("vetted", "approved", "certified", "recommended", "preferred", "best ",
          "top pick", "trusted", "endorse", "featured", "partner", "sponsored")

# ── published sources ────────────────────────────────────────────────────────
def _gr(U):
    rows = U["products"]
    if len(rows) != U["eligibleCount"]: die("garden-room universe product list != eligibleCount")
    def st(r):
        if r.get("irishAvailabilityConfirmationState") == "Yes": return "c"
        if r.get("noPublishedIrishRoute"): return "r"
        return "u"
    eligible = [(r["organisation"], r["id"], r["productName"], r.get("productType") or "", st(r)) for r in rows]
    header = {"products": U["eligibleCount"], "makers": U["organisationCount"],
              "confirmed": U["confirmedIrishAvailabilityCount"]}
    return eligible, set(), {r["organisation"] for r in rows}, header

def _ah(A):
    rows = A["products"]
    el = [q for q in rows if (q.get("qualification") or {}).get("state") == "ELIGIBLE"]
    held = {q["id"] for q in rows if (q.get("qualification") or {}).get("state") != "ELIGIBLE"}
    def st(q): return "c" if (q.get("irish") or {}).get("state") == "CONFIRMED" else "u"
    eligible = [(q["organisation"], q["id"], q["productName"], "", st(q)) for q in el]
    header = {"products": A["eligibleCount"]}
    # THE PUBLICATION GATE, READ HERE TOO (14 Oct 2026). An artefact that
    # declares the gate is read fail-closed: a product that is not exactly
    # PUBLISHABLE is held, never listed. G1 then refuses the build if the
    # header counted it, rather than quietly showing fewer.
    if A.get("publicationGate"):
        gated = {q["id"] for q in el if q.get("publicVisibility") != "PUBLISHABLE"}
        held |= gated
        eligible = [e for e in eligible if e[1] not in gated]
    return eligible, held, {q["organisation"] for q in rows}, header

def _wl(W):
    # The wellness universe (DISC-001 Garden Retreat). Public = ELIGIBLE AND
    # PUBLISHABLE, read from the record itself; the header's eligibleCount
    # counts exactly that, so G1 holds the two together.
    if not W.get("publicationGate"): die("the wellness universe does not declare the publication gate")
    rows = W["products"]
    pub = [q for q in rows if (q.get("qualification") or {}).get("state") == "ELIGIBLE"
           and q.get("publicVisibility") == "PUBLISHABLE"]
    held = {q["id"] for q in rows} - {q["id"] for q in pub}
    def st(q): return "c" if (q.get("irish") or {}).get("state") == "CONFIRMED" else "u"
    # Sixth element (14 Oct 2026): the kinds a product carries and a price
    # line, both composed here from the published record only.
    def ptype(q):
        ks = q.get("kinds") or []
        if "combination" in ks:   # one building that is both: Atlas's own type
            return q.get("productType") or KIND_LABEL["combination"]
        if len(ks) > 1:   # dual-use (WILD TUB): say so rather than pick one
            return " or ".join(KIND_LABEL[k] for k in ks).capitalize()
        return q.get("productType") or KIND_LABEL.get((ks or [""])[0], "")
    eligible = [(q["organisation"], q["id"], q["productName"], ptype(q), st(q),
                 {"kinds": q.get("kinds") or [], "price": price_line(q.get("price") or {}),
                  "nav": product_nav(q)})
                for q in pub]
    header = {"products": W["eligibleCount"], "makers": W["organisationCount"],
              "kindCounts": W.get("kindCounts") or {},
              "kindOrganisationCounts": W.get("kindOrganisationCounts") or {}}
    return eligible, held, {q["organisation"] for q in rows if q.get("organisation")}, header

# ── PRODUCT NAVIGATION, PROVED HERE (14 Oct 2026) ─────────────────────────────
# Founder brief "Garden Retreat — final pre-launch corrections", item 1: the
# smallest safe change. Nothing is allowed by default. A product gets
#   href  the maker's own product page, ONLY if that exact URL is VERIFIED in
#         atlas-tools/maker-product-links-v1.json (HTTPS, on a domain that
#         file attributes to THIS maker, HTTP 200, same-host same-path
#         redirects only, no query or fragment, and the page names the
#         product). REVISED 14 Oct 2026 (controlled text-only publication
#         expansion, item 3): an ordinary link to a maker's own public product
#         page no longer needs a supplier permission state -- "do not require
#         an invented supplier permission state for an ordinary link" -- but it
#         needs verified evidence, and arbitrary domains stay impossible;
#   img   ONLY images enumerated in that maker's approved_assets for this
#         exact product code, under a grant whose scope includes "imagery"
#         and whose asset approval is APPROVED; each with its kind label
#         (a visualisation's alt must say so) and the required credit.
# Every published product URL was fetched on 14 Oct 2026 and returned 200 at
# its own address.
RIGHTS = ROOT / "image-rights-records.json"
_RIGHTS = None
# Natural pixel sizes of the four OGNYX assets (fetched 14 Oct 2026), so the
# page reserves their space and nothing jumps when they load.
IMG_DIMS = {"recdcMBs7onIACLiO": (1024, 1026), "recOfcMW6ZjQh8PHj": (1024, 1031),
            "reczY9wkymWQg9df3": (1024, 1022), "reccvs54yEV48AY7R": (1024, 1024)}


def rights_row(org):
    global _RIGHTS
    if _RIGHTS is None:
        _RIGHTS = {r["organisation_name"]: r for r in
                   json.loads(RIGHTS.read_text(encoding="utf-8"))["records"]}
    return _RIGHTS.get(org)


def _host(u):
    m = re.match(r"https://([^/?#]+)(/|$)", u or "")
    return m.group(1).lower() if m else None


LINKS = ROOT / "atlas-tools" / "maker-product-links-v1.json"
_LINKS = None
SAFE_URL = re.compile(r"https://[A-Za-z0-9.-]+/[A-Za-z0-9._~/%+-]*")


def links_doc():
    global _LINKS
    if _LINKS is None:
        _LINKS = json.loads(LINKS.read_text(encoding="utf-8"))
    return _LINKS


def verified_link(pid, org, url):
    """The site label to show when this product's own page is VERIFIED for
    this maker at exactly this URL, else None."""
    D = links_doc()
    e = D["links"].get(pid) or {}
    doms = (D["makerDomains"].get(org) or {}).get("domains") or []
    if (e.get("state") != "VERIFIED" or e.get("organisation") != org or not url
            or e.get("url") != url or e.get("status") != 200 or not SAFE_URL.fullmatch(url)
            or _host(url) not in doms):
        return None
    h = _host(url)
    return h[4:] if h.startswith("www.") else h


def product_nav(q):
    nav = {}
    u = q.get("productUrl")
    site = verified_link(q.get("id"), q.get("organisation"), u)
    if site:
        nav["href"], nav["site"] = u, site
    # IMAGES ARE STILL GOVERNED BY THE RIGHTS RECORD ALONE. A public-
    # information listing has no rights record, so it can never reach here.
    r = rights_row(q.get("organisation"))
    if not r or r.get("public_visibility") != "PUBLISHABLE":
        return nav
    perm = r.get("permission") or {}
    if perm.get("state") != "GRANTED" or "feature" not in (perm.get("scope") or []):
        return nav
    dom = (r.get("permitted_domain") or "").lower()
    if ("imagery" in (perm.get("scope") or []) and r.get("asset_approval_state") == "APPROVED"
            and r.get("required_credit")):
        imgs = []
        for a in r.get("approved_assets") or []:
            if a.get("product_code") != q.get("productCode"):
                continue
            if _host(a.get("url")) not in (dom, "www." + dom) or a.get("atlas_asset") not in IMG_DIMS:
                die("an approved asset is off-domain or has no recorded size: %r" % a.get("atlas_asset"))
            kind = {"photograph": "Photograph", "visualisation": "Visualisation"}[a["kind"]]
            if not a.get("alt", "").startswith(kind):
                die("asset %s alt text does not open with its kind (%s)" % (a["atlas_asset"], kind))
            w, h = IMG_DIMS[a["atlas_asset"]]
            imgs.append({"src": a["url"], "alt": a["alt"], "kind": kind, "w": w, "h": h,
                         "credit": r["required_credit"], "creditHref": "https://www.%s/" % dom})
        if imgs:
            nav["img"] = imgs
    return nav


KIND_LABEL = {"sauna": "Outdoor sauna", "hot-tub": "Hot tub", "cold-plunge": "Cold plunge",
              "combination": "Sauna and hot tub building"}


def price_line(pr):
    """A short, homeowner-readable price line from a VERIFIED_NUMERIC_PRICE
    record. Its VAT position is carried over exactly; nothing is inferred."""
    if pr.get("state") != "VERIFIED_NUMERIC_PRICE" or pr.get("currency") != "EUR":
        return ""
    amt = "€{:,.0f}".format(pr["amount"]) if float(pr["amount"]).is_integer() else "€{:,.2f}".format(pr["amount"])
    basis = pr.get("basis") or ""
    lead = "From " + amt if pr.get("type") == "Starting From" else amt
    if "for the range" in basis:
        lead += " (range price)"
    if "including VAT" in basis:
        return lead + " incl. VAT"
    if "excluding VAT" in basis:
        return lead + " excl. VAT"
    return lead + " · VAT not stated"

SOURCES = {
    "garden-room-universe-v1": {
        "file": "garden-room-recommendation-universe-v1.json", "read": _gr,
        # your-plot.html?product= resolves the Garden Room pool, so these
        # products have a PlotNua product page.
        "productPage": "your-plot.html?product={id}",
    },
    "additional-home-universe-v1": {
        "file": "additional-home-universe-v1.json", "read": _ah,
        # The deep link resolves the Garden Room pool only and fails closed
        # for a garden home, so these products have NO product page yet.
        "productPage": None,
    },
    "wellness-universe-v1": {
        "file": "wellness-universe-v1.json", "read": _wl,
        "productPage": None,
        # NO JOURNEY YET, SAID PLAINLY. Garden Retreat's property check is
        # "being prepared" (its own page says so) and no product page resolves
        # a wellness product, so there is nowhere honest to send anyone. The
        # tab therefore lists products as TEXT with no onward link, rather
        # than routing to a journey that would not show them.
        "noJourneyYet": True,
    },
}
# Journeys a tab may route to when its products have no product page.
ALLOWED_ROUTES = {"your-plot.html?discovery=residential", "your-plot.html?discovery=garden-room"}

# ── per-Discovery configuration ──────────────────────────────────────────────
AVAIL_NOTE = ("Prices are as each maker publishes them. Confirm delivery and "
              "installation details directly with the supplier.")
PAGES = {
    "discovery-living-in-the-garden.html": {
        "kicker": "Makers and Products",
        "heading": "Explore makers and products",
        "intro": ("Discover real garden rooms and garden homes researched by PlotNua. Explore\n"
                  "      product details, published specifications and availability information before\n"
                  "      deciding what might work for your property."),
        "tabs": [
            {"key": "gardenRooms", "id": "rooms", "label": "Garden rooms",
             "nouns": ["garden room", "garden rooms"], "source": "garden-room-universe-v1"},
            {"key": "gardenHomes", "id": "homes", "label": "Garden homes",
             "nouns": ["garden home", "garden homes"], "source": "additional-home-universe-v1",
             "route": {"href": "your-plot.html?discovery=residential",
                       "note": "Garden homes are shown on PlotNua after a short property check.",
                       "label": "Check garden homes for your property"}},
        ],
        # (figure key, label). researchedMakers = union of organisations
        # across every source the page uses, held-only makers included as
        # research and never named.
        "headline": [("tab:gardenRooms", "garden rooms"), ("tab:gardenHomes", "garden homes"),
                     ("researchedMakers", "makers researched")],
        "noscript": ("search PlotNua&rsquo;s garden rooms and garden homes"),
        "after": "Garden room prices are hard to compare.",
        "before": "What would you like PlotNua to check?",
        "block_end": "  <!-- 7 · THE EVIDENCE LAYER.",
        "first_build_anchor": "  <!-- 6c · PLOTNUA-DISCOVERY-MAKERS-PHASE1",
        "css_anchor": "/* PLOTNUA A11Y VISUAL v1 · END */\n</style>",
        "keep_links": ('href="your-plot.html?discovery=residential"',
                       'href="your-plot.html?discovery=garden-room"'),
    },    # DISC-001 Garden Retreat. Founder decision 14 Oct 2026: "OGNYX public
    # integration — PROCEED". One tab over the wellness universe; products are
    # listed as text (see SOURCES: noJourneyYet). Inserted after "Where this is
    # sold in Ireland" and before the evidence section, on first build.
    "discovery-garden-retreat.html": {
        "kicker": "Makers and Products",
        "heading": "Explore makers and products",
        "intro": ("Saunas, hot tubs and cold plunges from makers whose published products PlotNua\n"
                  "      has checked. Makers are never ranked; open one to see its products and the\n"
                  "      prices it publishes."),
        # Three kind tabs over one universe (restructure brief 14 Oct 2026:
        # "Saunas, Hot Tubs, Cold Plunges"). Irish availability is not
        # established per product for any of them, so each tab says what a
        # homeowner should do rather than counting zero.
        "tabs": [
            {"key": "saunas", "id": "saunas", "label": "Saunas", "kinds": ["sauna"],
             "nouns": ["sauna", "saunas"], "source": "wellness-universe-v1",
             "availabilityNote": AVAIL_NOTE},
            {"key": "hotTubs", "id": "hot-tubs", "label": "Hot tubs", "kinds": ["hot-tub"],
             "nouns": ["hot tub", "hot tubs"], "source": "wellness-universe-v1",
             "availabilityNote": AVAIL_NOTE},
            {"key": "coldPlunges", "id": "cold-plunges", "label": "Cold plunges", "kinds": ["cold-plunge"],
             "nouns": ["cold plunge", "cold plunges"], "source": "wellness-universe-v1",
             "availabilityNote": AVAIL_NOTE},
        ],
        "headline": [("tab:saunas", "saunas"), ("tab:hotTubs", "hot tubs"), ("tab:coldPlunges", "cold plunges")],
        "noscript": "search PlotNua&rsquo;s saunas, hot tubs and cold plunges",
        # Restructure, 14 Oct 2026: the directory sits after "Could it work for
        # your property?" and before the practical considerations.
        "after": "<h2>Could it work for your property?</h2>",
        "before": "<h2>What you need to sort out</h2>",
        "insert_first_build": True,
        "first_build_anchor": '  <section class="article-section reveal" id="the-practical-part">',
        "block_end": '  <section class="article-section reveal" id="the-practical-part">',
        "css_anchor": "/* PLOTNUA A11Y VISUAL v1 · END */\n</style>",
        "keep_links": ('href="discovery-living-in-the-garden.html"',),
    },
}

def info_pages():
    src = SEARCH_BUILDER.read_text(encoding="utf-8")
    m = re.search(r"^SUPPLIER_INFO_PAGES = (\{.*?^\})", src, re.S | re.M)
    if not m: die("SUPPLIER_INFO_PAGES not found in build-search-index.py")
    return ast.literal_eval(m.group(1))

# Display-name overrides seen across EVERY page in one run. Checked once, in
# main(): an override must name a product some page lists, not every page.
SEEN_OVERRIDES = set()

# ── data for one page ────────────────────────────────────────────────────────
def load(P):
    cache, seen_override, all_orgs, held_all, tabs = {}, set(), set(), set(), []
    def name(pid, atlas_name):
        o = DISPLAY_NAME_BY_ID.get(pid)
        if not o: return atlas_name
        if atlas_name != o["atlas"]:
            die("display-name override for %s is stale: Atlas now says %r" % (pid, atlas_name))
        seen_override.add(pid)
        return o["display"]
    for T in P["tabs"]:
        S = SOURCES.get(T["source"])
        if not S: die("tab %r names a source that is not a published eligibility file" % T["key"])
        if T["source"] not in cache:
            cache[T["source"]] = S["read"](json.loads((ROOT / S["file"]).read_text(encoding="utf-8")))
        eligible, held, orgs, header = cache[T["source"]]
        all_orgs |= orgs; held_all |= held
        if T.get("kinds"):
            # A kind tab (14 Oct 2026): exactly the source's products of that
            # kind, held to the universe's own per-kind header.
            if len(T["kinds"]) != 1: die("tab %r: a kind tab names exactly one kind" % T["key"])
            k = T["kinds"][0]
            if k not in header.get("kindCounts", {}): die("tab %r: the source declares no count for kind %r" % (T["key"], k))
            eligible = [e for e in eligible if len(e) > 5 and k in e[5]["kinds"]]
            header = {"products": header["kindCounts"][k], "makers": header["kindOrganisationCounts"][k]}
        by = {}
        for e in eligible:
            org, pid, pname, ptype, st = e[:5]
            row = [pid, name(pid, pname), ptype, st]
            if len(e) > 5 and e[5].get("price"):
                row.append(e[5]["price"])
            if len(e) > 5 and e[5].get("nav"):
                if len(row) == 4:
                    row.append("")
                row.append(e[5]["nav"])
            by.setdefault(org, []).append(row)
        makers = [{"m": DISPLAY_ALIAS.get(k, k), "p": sorted(v, key=lambda x: x[1].lower())}
                  for k, v in sorted(by.items(), key=lambda kv: kv[0].lower())]
        figures = {"products": len(eligible), "makers": len(by),
                   "confirmed": sum(1 for e in eligible if e[4] == "c"),
                   "noRoute": sum(1 for e in eligible if e[4] == "r")}
        cfg = {"key": T["key"], "nouns": T["nouns"], "figures": figures, "makers": makers,
               "productLink": S["productPage"]}
        if T.get("availabilityNote"):
            if figures["confirmed"]: die("tab %r: an availability note replaces a count of zero only" % T["key"])
            cfg["availabilityNote"] = T["availabilityNote"]
        if not S["productPage"]:
            if T.get("route"):
                if S.get("noJourneyYet"): die("tab %r routes to a journey its source says does not exist" % T["key"])
                cfg["route"] = T["route"]
            elif not S.get("noJourneyYet"):
                die("tab %r has no product page and no route" % T["key"])
        elif T.get("route"):
            die("tab %r links products; it must not also carry a route" % T["key"])
        tabs.append({"T": T, "cfg": cfg, "header": header, "eligible_ids": {e[1] for e in eligible}})
    SEEN_OVERRIDES.update(seen_override)
    return tabs, len(all_orgs), held_all

# ── markup ───────────────────────────────────────────────────────────────────
def section(P, tabs, researched):
    figs = {"researchedMakers": researched}
    for t in tabs: figs["tab:" + t["T"]["key"]] = t["cfg"]["figures"]["products"]
    head = "\n".join(f'      <div><span class="mx-fig">{figs[k]}</span><span class="mx-fig-l">{html.escape(lab)}</span></div>'
                     for k, lab in P["headline"])
    first = tabs[0]["T"]
    btn = []
    for i, t in enumerate(tabs):
        extra = "" if i == 0 else ' tabindex="-1"'
        btn.append(f'        <button type="button" class="mx-tab" role="tab" id="mx-t-{t["T"]["id"]}" '
                   f'aria-selected="{"true" if i == 0 else "false"}" aria-controls="mx-pane" data-k="{t["T"]["key"]}"'
                   f'{extra}>{html.escape(t["T"]["label"])} <span class="mx-n">{t["cfg"]["figures"]["products"]}</span></button>')
    btns = "\n".join(btn)
    config = {"initial": 6, "tabs": [t["cfg"] for t in tabs]}
    pages = " Product pages open within PlotNua." if any(t["cfg"]["productLink"] for t in tabs) else ""
    if any(len(p) > 5 and p[5].get("href") for t in tabs for m in t["cfg"]["makers"] for p in m["p"]):
        pages += (" Listings come from each maker&rsquo;s own published product pages;"
                  " &ldquo;See it on&rdquo; opens that page in a new tab.")
    credits = image_credits(tabs)
    payload = json.dumps(config, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    return f'''  <!-- 6c · {MARK} · Founder decisions 13 Oct 2026. Shared component
       (maker-explorer.js / maker-explorer.css) configured for this page by
       atlas-tools/build-maker-explorer.py from published eligibility files;
       do not hand-edit. -->
  <section class="article-section reveal" id="explore-makers" data-pn-maker-explorer>
    <div class="kicker">{html.escape(P["kicker"])}</div>
    <h2>{html.escape(P["heading"])}</h2>
    <p>{P["intro"]}</p>

    <div class="mx-figs">
{head}
    </div>

    <div class="mx" id="mx">
      <div class="mx-tabs" role="tablist" aria-label="Product type">
{btns}
      </div>
      <div class="mx-pane" id="mx-pane" role="tabpanel" aria-labelledby="mx-t-{first["id"]}">
        <p class="mx-line" id="mx-line"></p>
        <ul class="mx-legend" id="mx-legend"></ul>
        <div class="mx-top" id="mx-top" hidden><button type="button" class="mx-btn" id="mx-less-top">Show fewer makers</button></div>
        <div class="mx-tools" id="mx-tools" hidden>
          <input class="mx-find" id="mx-find" type="search" placeholder="Find a maker" aria-label="Find a maker" autocomplete="off">
          <div class="mx-chips" id="mx-chips" role="group" aria-label="Irish availability">
            <button type="button" class="mx-chip" data-f="all" aria-pressed="true">All</button>
            <button type="button" class="mx-chip" data-f="c" aria-pressed="false">Confirmed</button>
            <button type="button" class="mx-chip" data-f="u" aria-pressed="false">Not yet confirmed</button>
          </div>
        </div>
        <p class="mx-order" id="mx-order"></p>
        <ul class="mx-grid" id="mx-grid"></ul>
        <div class="mx-more"><button type="button" class="mx-btn" id="mx-all"></button><span class="mx-order" id="mx-shown"></span></div>
        <noscript><p class="mx-line">The maker list needs JavaScript. You can still
          <a href="search.html">{P["noscript"]}</a>.</p></noscript>
      </div>
    </div>


    <p class="mx-foot">Only products PlotNua&rsquo;s research currently makes public are listed;
      products still being checked are not shown. Makers are not ranked, and PlotNua has no
      commercial arrangement with any maker listed.{pages}</p>
{credits}
    <script type="application/json" class="pn-mx-config" id="mx-data">{payload}</script>
    {JS_TAG}
  </section>

'''

def image_credits(tabs):
    """One static credit line per maker whose authorised images the
    directory can show: the credit and the link back are grant conditions,
    so they are on the page itself, not only inside a drawer."""
    seen = {}
    for t in tabs:
        for m in t["cfg"]["makers"]:
            for p in m["p"]:
                for im in (p[5].get("img") or []) if len(p) > 5 else []:
                    seen[im["creditHref"]] = im["credit"]
    out = ""
    for href, credit in sorted(seen.items()):
        out += ('    <p class="mx-foot mx-credit">Product images: <a href="%s" target="_blank" '
                'rel="noopener noreferrer">%s</a>, shown as supplied. Images labelled '
                '&ldquo;Visualisation&rdquo; are computer-generated, not photographs.</p>\n'
                % (href, html.escape(credit)))
    return out


def sha(p): return hashlib.sha256((ROOT / p).read_bytes()).hexdigest()

# ── build one page ───────────────────────────────────────────────────────────
def build(fname, P, src):
    # G11a the shared implementation is exactly the pinned one
    for f, want in PINS.items():
        if not (ROOT / f).exists(): die("G11 shared file missing: " + f)
        if sha(f) != want: die("G11 %s differs from its pinned sha256; re-pin deliberately" % f)
    head_css = src.split("</head>")[0]
    for tok in HOST_TOKENS:
        if tok + ":" not in head_css: die("G11 host page does not define token " + tok)

    # strip what a previous build left: v1 inline CSS, or the v2 link
    if V1_CSS_MARK in src:
        a = src.find("/* ==== " + V1_CSS_MARK + " · generated by")
        b = src.find("/* ==== " + V1_CSS_MARK + " · END ==== */")
        if a < 0 or b < 0 or src[a - 1] != "\n": die("existing v1 CSS block shape unexpected")
        src = src[:a - 1] + src[b + len("/* ==== " + V1_CSS_MARK + " · END ==== */\n"):]
    if src.count(CSS_LINK) == 1:
        src = src.replace(P["css_anchor"] + "\n" + CSS_LINK, P["css_anchor"], 1)
        if CSS_LINK in src: die("existing stylesheet link not where the builder puts it")
    existing = MARK in src
    start = src.find("  <!-- 6c · " + MARK) if existing else src.find(P["first_build_anchor"])
    end = src.find(P["block_end"])
    # A page whose first build REPLACES a placeholder section (Living in the
    # Garden) has one section between the anchors; a page whose first build
    # INSERTS (insert_first_build) has none. Every later build has exactly one.
    want = 0 if (P.get("insert_first_build") and not existing) else 1
    if start < 0 or end < 0 or end < start: die("explorer block anchors not found")
    if src[start:end].count("<section") != want: die("block shape unexpected")

    tabs, researched, held_ids = load(P)
    ip = info_pages()
    new_block = section(P, tabs, researched)
    out = src[:start] + new_block + src[end:]
    if out.count(P["css_anchor"]) != 1: die("CSS anchor not found exactly once")
    out = out.replace(P["css_anchor"], P["css_anchor"] + "\n" + CSS_LINK, 1)

    blk = new_block
    visible = re.sub(r"<script.*?</script>", " ", blk, flags=re.S)
    visible = re.sub(r"<!--.*?-->", " ", visible, flags=re.S)
    vtext = html.unescape(re.sub(r"<[^>]+>", " ", visible)).lower()
    js = (ROOT / SHARED_JS).read_text(encoding="utf-8")
    cfgs = [t["cfg"] for t in tabs]

    # G1 counts agree with each source's own header
    for t in tabs:
        F, H = t["cfg"]["figures"], t["header"]
        for k, v in H.items():
            if F[k] != v: die("G1 %s %s=%d disagrees with the universe header %d" % (t["T"]["key"], k, F[k], v))
        if sum(len(m["p"]) for m in t["cfg"]["makers"]) != F["products"]: die("G1 products not all listed")
        if f'<span class="mx-fig">{F["products"]}</span>' not in blk: die("G1 headline figure missing")
    if any(k == "researchedMakers" for k, _ in P["headline"]) and \
            f'<span class="mx-fig">{researched}</span>' not in blk:
        die("G1 makers researched missing")
    # G2 no held or excluded product; each tab lists exactly its eligible set
    for hid in held_ids:
        if hid in out: die("G2 a held product id appears on the page: " + hid)
    for t in tabs:
        listed = {p[0] for m in t["cfg"]["makers"] for p in m["p"]}
        if listed != t["eligible_ids"]: die("G2 %s does not list exactly its eligible set" % t["T"]["key"])
    # G10 no research note in a displayed name
    for c in cfgs:
        for m in c["makers"]:
            if ANNOTATION_RE.search(m["m"]): die("G10 maker name carries a note: " + m["m"])
            for p in m["p"]:
                if ANNOTATION_RE.search(p[1]): die("G10 product name carries a research note: " + p[1])
    # G3 no external link; product links only where the source has a product page.
    # NARROWED 14 Oct 2026, not relaxed: the static block may carry an external
    # link only as an image credit's link back, and only to the domain of a
    # maker whose images the directory actually shows. Per-product links live
    # in the configuration and are re-proved below against the rights record.
    credit_hrefs = {im["creditHref"] for c in cfgs for m in c["makers"] for p in m["p"]
                    if len(p) > 5 for im in (p[5].get("img") or [])}
    for h in re.findall(r'href="([^"]+)"', blk):
        if re.match(r"[a-z]+:", h) or h.startswith("//"):
            if h not in credit_hrefs: die("G3 external link: " + h)
            continue
        if not (ROOT / h.split("?")[0]).exists(): die("G3 link target missing: " + h)
    for c in cfgs:
        for m in c["makers"]:
            for p in m["p"]:
                if len(p) <= 5:
                    continue
                X = p[5]
                if set(X) - {"href", "site", "img"}: die("G3 unexpected navigation field on " + p[0])
                # Re-derived from the rights record, independently of product_nav().
                R = rights_row(m["m"]) or {}
                perm = R.get("permission") or {}
                dom = (R.get("permitted_domain") or "").lower()
                if X.get("img") and (R.get("public_visibility") != "PUBLISHABLE"
                                     or perm.get("state") != "GRANTED"):
                    die("G3 images for a maker whose rights record is not PUBLISHABLE: " + m["m"])
                # Re-derived from the link evidence, independently of product_nav().
                if X.get("href"):
                    E = links_doc()["links"].get(p[0]) or {}
                    doms = (links_doc()["makerDomains"].get(m["m"]) or {}).get("domains") or []
                    if E.get("state") != "VERIFIED" or E.get("url") != X["href"] or E.get("organisation") != m["m"]:
                        die("G3 a product link not VERIFIED for this product and maker: " + p[0])
                    if _host(X["href"]) not in doms:
                        die("G3 a product link off the maker's own domain: " + X["href"])
                if X.get("img"):
                    allowed = {a["url"] for a in R.get("approved_assets") or []}
                    for im in X["img"]:
                        if im["src"] not in allowed: die("G3 an image not in the maker's approved assets: " + im["src"][:80])
                        if im["credit"] != R.get("required_credit"): die("G3 an image without the required credit")
                        if im["kind"] == "Visualisation" and not im["alt"].startswith("Visualisation"):
                            die("G3 a visualisation not labelled as one")
                if X.get("href"):
                    host = _host(X["href"])
                    if not host or not X["href"].startswith("https://") or host.replace("www.", "", 1) != X.get("site"):
                        die("G3 product link label does not match its destination: " + X["href"])
                    if not re.fullmatch(r"https://[A-Za-z0-9.-]+/[A-Za-z0-9._~/%+-]*", X["href"]):
                        die("G3 product link carries a query, fragment or unexpected character: " + X["href"])
    if "http" in js or "window.open" in js or "your-plot.html" in js:
        die("G3 the shared script may compose links only from configuration")
    if "http" in js or "window.open" in js or "your-plot.html" in js:
        die("G3 the shared script may compose links only from configuration")
    for t in tabs:
        c, S = t["cfg"], SOURCES[t["T"]["source"]]
        if c["productLink"] != S["productPage"]: die("G3 %s product link is not its source's product page" % c["key"])
        if c["productLink"] and c["productLink"] != "your-plot.html?product={id}":
            die("G3 product link must be the governed deep link")
        if c.get("route"):
            if c["route"]["href"] not in ALLOWED_ROUTES: die("G3 route not an allowed PlotNua journey")
            if not (ROOT / c["route"]["href"].split("?")[0]).exists(): die("G3 route target missing")
    # G4 no storage, fetch, analytics or URL state in the shared script
    for bad in ("localStorage", "sessionStorage", "indexedDB", "fetch(", "XMLHttpRequest",
                "gtag", "dataLayer", "history.", "document.cookie", "sendBeacon",
                "location.href", "location.assign", "location.replace", "location.search",
                "location.reload", "pushState", "replaceState"):
        if bad in js: die("G4 forbidden in the shared script: " + bad)
    # NARROWED 14 Oct 2026: the one URL READ permitted is the fragment, exactly
    # once, and it is never written.
    if js.count("location.") != 1 or js.count("window.location.hash || ''") != 1:
        die("G4 the script may read window.location.hash once and touch no other URL state")
    if re.search(r"location\.hash\s*=[^=]", js): die("G4 the script writes the URL fragment")
    if "/^#p-(rec[A-Za-z0-9]{14})$/" not in js: die("G4 the fragment is not matched against the product-id pattern")
    # G5 A-Z directory; the only order at rest is a shuffle
    for c in cfgs:
        names = [m["m"].lower() for m in c["makers"]]
        if names != sorted(names): die("G5 directory is not A to Z")
    if "Math.random" not in js or ".sort(" in js: die("G5 initial order must be a shuffle, never a sort")
    # G6 no endorsement vocabulary: page text, configuration strings, script strings
    cfg_text = " ".join([" ".join(c["nouns"]) + " " + " ".join((c.get("route") or {}).values()) + " " +
                         c.get("availabilityNote", "") + " " +
                         " ".join(p[4] for m in c["makers"] for p in m["p"] if len(p) > 4) for c in cfgs])
    texts = (vtext + " " + cfg_text + " " + " ".join(re.findall(r"'([^']*)'", js))).lower()
    for w in BANNED:
        if w in texts: die("G6 banned word: " + w.strip())
    # G7 no special supplier placement; TRIQ stays published and in Search
    if "mx-info" in blk or "Manufacturer information" in blk: die("G7 a manufacturer box is back")
    sitemap = (ROOT / "sitemap.xml").read_text(encoding="utf-8")
    for f in ip:
        if f in blk: die("G7 supplier information page linked from the explorer: " + f)
        if not (ROOT / f).exists(): die("G7 supplier information page missing: " + f)
        if "https://plotnua.ie/" + f not in sitemap: die("G7 supplier information page left the sitemap: " + f)
    if "triq-cube.html" not in ip: die("G7 TRIQ QUBE (triq-cube.html) must stay in Search (SUPPLIER_INFO_PAGES)")
    # G8 no area figure in the page's own prose (Cluster 1 L1)
    if re.search(r"\d\s*(m²|m&sup2;|square metres)", visible): die("G8 an area figure would reach the page")
    # G9 nothing outside the block and the stylesheet link changes; placement
    rest_before = src[:start] + src[end:]
    rest_after = out.replace(new_block, "", 1).replace(P["css_anchor"] + "\n" + CSS_LINK, P["css_anchor"], 1)
    if rest_before != rest_after: die("G9 something outside the block and stylesheet link changed")
    for keep in P["keep_links"]:
        if rest_before.count(keep) < 1 or out.replace(new_block, "", 1).count(keep) != rest_before.count(keep):
            die("G9 Property Check link changed")
    if not (out.index(P["after"]) < out.index('id="explore-makers"') < out.index(P["before"])): die("G9 placement")
    if out.count('id="explore-makers"') != 1: die("G9 duplicate section id")
    # G11b exactly one stylesheet link and one script; the link sits in <head>
    if out.count(CSS_LINK) != 1 or out.count(JS_TAG) != 1: die("G11 shared assets must be included exactly once")
    if out.index(CSS_LINK) > out.index("</head>"): die("G11 stylesheet link must be in <head>")
    print(f"  {fname}: " + ", ".join(f'{c["key"]} {c["figures"]}' for c in cfgs) + f", researched makers {researched}")
    return out

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "--check"
    for fname, P in PAGES.items():
        page = ROOT / fname
        out = build(fname, P, page.read_text(encoding="utf-8"))
        if mode == "--apply":
            page.write_text(out, encoding="utf-8")
    if not set(DISPLAY_NAME_BY_ID) <= SEEN_OVERRIDES:
        die("display-name override for a product that is not publicly listed: %s"
            % sorted(set(DISPLAY_NAME_BY_ID) - SEEN_OVERRIDES))
    print(("APPLIED" if mode == "--apply" else "CHECK OK") + f" — G1-G11 pass for {len(PAGES)} page(s)")

if __name__ == "__main__":
    main()
