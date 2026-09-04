#!/usr/bin/env python3
"""
PlotNua — Garden Room Match Qualification v1 (DRY RUN).

Reads every Garden Room in Atlas and classifies it into one of four states, so
the Match Engine can rank on evidence instead of on a certification flag that
no product has ever held.

    ELIGIBLE — HIGH CONFIDENCE
    ELIGIBLE — WITH CAVEAT
    ELIGIBLE — LIMITED EVIDENCE
    EXCLUDED — HARD BLOCKER

THE ONE RULE EVERYTHING ELSE SERVES: UNKNOWN IS NEVER FALSE.

    Missing evidence lowers confidence. It never excludes. A product is hard-
    excluded only where evidence positively establishes a reason it cannot be
    recommended — never where evidence is simply absent.

    This is why the previous universe is obsolete: recommendation-universe-v1
    withheld 199 of 239 products because Irish availability was UNKNOWN. That
    turned absence of evidence into a verdict.

WHAT THIS SCRIPT DOES NOT DO
    No Airtable writes of any kind. No Standards field. No certification. No
    touching of recommendation-universe-v1.json, atlas-match-pool.json or
    atlas-recognition-pool.json. In dry-run mode (the default) it writes only
    to an output directory you name, never to a production path.

WHY IRISH AVAILABILITY IS PARSED FROM TEXT, AND WHY THAT IS FLAGGED
    The schema provides Product Feature Values.Confirmation State as a genuine
    four-state field (Yes / Yes - Conditional / No / Unknown), and its own
    description says the engine must NOT treat Unknown as No. Measured against
    live Atlas on 3 September 2026, that field is unpopulated on the Irish
    Availability rows sampled; the evidence is carried in Value Text as prose
    with an uppercase classifier lead, e.g.

        "AVAILABLE ACROSS IRELAND. Irish manufacturer, Dundalk…"
        "AVAILABILITY UNKNOWN. No supplier-attributable delivery coverage…"
        "REPUBLIC OF IRELAND UNCONFIRMED. Estonian manufacturer…"

    ORDER OF EVIDENCE (revised by the 3 September diagnostic). A POSITIVE
    Confirmation State is decisive. Otherwise Value Text is read first, and a
    legacy negative Confirmation State is honoured only where the text
    explicitly establishes that the Republic cannot be served. Reading the
    legacy flag first is what produced the incoherence the diagnostic found:
    six products hard-excluded on a populated checkbox while ~48 carrying the
    same UK-ONLY prose stayed eligible because theirs was blank.

    Any lead phrase not in the vocabulary below resolves to UNKNOWN — never to
    unavailable — and is counted in unclassifiedIrishAvailabilityCount so the
    blind spot is visible rather than silent. UK-only coverage resolves to
    UNKNOWN carrying `noPublishedIrishRoute`. Fixing the underlying field is
    Atlas work, not qualification work, and is reported rather than papered
    over.

Standard library only, matching .github/scripts/atlas_stats.py.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

# ── Atlas addressing ─────────────────────────────────────────────────────────
# The base id is an identifier, not a credential: useless without a token.
BASE_ID = "appoLZFWesvoPhZGR"                 # PlotNua Atlas Core

T_PRODUCTS   = "tblMiUcO4OT9ia2aE"
T_PRICING    = "tblqsjmkTrwSct7gv"
T_AVAIL      = "tblP1d5lgKxxhkBkj"
T_FEATVALS   = "tbl7wGyTgJ2mzjdOh"
T_FEATURES   = "tblH2EpBiV9bt1rdD"
T_ORGS       = "tblngwmviAcWxFKsW"

GARDEN_ROOMS = "Garden Rooms"
RULE_VERSION = "garden-room-qualification-v1"
SCHEMA       = "plotnua.garden-room-recommendation-universe"
VERSION      = "1.0.0-dryrun"

API = "https://api.airtable.com/v0"
PAGE_SIZE = 100
RETRIES = 4

# ── the exact fields read, declared explicitly ───────────────────────────────
# Nothing is read that is not named here. "    Sources" carries leading spaces
# in Atlas; that is the real field name, not a typo.
PRODUCT_FIELDS = [
    "Product Name", "Product Code", "Product Type", "Product Category",
    "Status", "Verification Status", "Organisation", "Brand", "Product URL",
    "Description", "Notes", "Standards", "    Sources",
    "Atlas Product Certification Audit v1", "Results Eligibility v1",
    "Artist's Studio Match Status",
]
PRICING_FIELDS = [
    "Product", "Base Price", "Price From", "Price To", "Currency",
    "Price Type", "Price Includes VAT", "Status", "Primary Price",
    "Evidence Scope", "Known Exclusions", "Last Price Check",
]
AVAIL_FIELDS = [
    "Product", "Availability", "Status", "Evidence Scope",
    "Availability URL", "Notes",
]
FEATVAL_FIELDS = [
    "Product", "Feature", "Value Text", "Value Number", "Unit",
    "Value Boolean", "Confirmation State", "Evidence Scope", "Status",
]
FEATURE_FIELDS = ["Feature Name", "Feature Code", "Feature Group", "Data Type"]

# Features whose values the universe carries forward for ranking. Matched on
# lowercased name, because Atlas holds near-duplicates ("Irish availability"
# FEAT-0021 and "Irish Availability" FEA-025 both exist and both are read).
# ---- ISSUE 005 PIECE D4b — THE DETAIL EVIDENCE CONTRACT --------------------
# Long-form Atlas evidence a homeowner reads only AFTER opening Product Detail.
# It is emitted into garden-room-detail-evidence-v1.json and fetched lazily, so
# it never enters the file every visitor downloads.
#
# THIS MAP IS THE EXTENSION POINT. Planning Considerations, Best For, Strengths
# and Typical Homeowner are expected to join it later; adding one is a single
# line here and needs no change to the file shape, the validator or the reader.
# D4b DELIBERATELY ADDS NONE OF THEM.
DETAIL_FEATURES_WANTED = {
    "considerations":          "considerations",
    # ---- ISSUE 005 PIECE E2 — the remaining Decision Intelligence layer -----
    # Measured across all 2,327 records this Piece. Every one is CARRIED here;
    # what the homeowner is shown is decided in the page, per category, on the
    # evidence below. Nothing is discarded, so a later presentation decision
    # needs no generator change.
    #
    #                          records   HOMEOWNER IMPLICATION:   presentable?
    #   Planning Considerations   467          451  (96.6%)        yes
    #   Best For                  465          352  (75.7%)        yes
    #   Alternatives              465          298  (64.1%)        yes, as evidence
    #   Typical Homeowner         465            0   (0.0%)        only NOT FOR: / NOT THIS BUYER:
    #   Strengths                 465           36   (7.7%)        NO — carried, withheld
    "planning considerations": "planningConsiderations",
    "best for":                "bestFor",
    "strengths":               "strengths",
    "typical homeowner":       "typicalHomeowner",
    "alternatives":            "alternatives",
}

# ISSUE 005 PIECE E2 — ONE PARTITION PER CATEGORY, PLUS PROVENANCE.
# A homeowner reading a Consideration must not download Alternatives to do it.
# Six small files, never 490: the brief's explicit ceiling. The index below is
# what the runtime reads to learn which partitions exist, so the page never
# guesses a filename and a category can be added or removed without a page
# change.
DETAIL_PARTITION_PREFIX = "garden-room-detail-"
DETAIL_PARTITION_SUFFIX = "-v1.json"
DETAIL_INDEX_FILE = "garden-room-detail-index-v1.json"
# Reserved, not implemented in E2: "suppliers" needs an Organisations field-name
# forensic before anything can be exported without guessing. The slot exists so
# that adding it later is an entry here, not an architecture change.
DETAIL_PROVENANCE_KEY = "sources"

# ISSUE 005 PIECE E2a — THE SUPPLIER EVIDENCE CONTRACT.
#
# Keyed by CANONICAL ORGANISATION RECORD ID, in its own partition. 188 supplier
# objects, not one duplicated across each of its ~30 products. Products already
# carry `organisationEvidence: [{id, name}]`, so the join is by id and needs no
# fuzzy supplier matching and no invented identity.
#
# Each entry is a label read out of `Headquarters`, exactly. A label absent from
# this map is a label the homeowner cannot see, which is how CONTACT: stays out.
DETAIL_SUPPLIER_KEY = "suppliers"
SUPPLIER_LABELS = {
    # exported key          Headquarters label        coverage /188
    "contractingEntity":    "LEGAL ENTITY",         #   51   27.1%
    "installationModel":    "INSTALLATION COVERAGE",#  179   95.2%
    "irishPresence":        "IRISH PRESENCE",       #  179   95.2%
    "deliveryCoverage":     "DELIVERY COVERAGE",    #  measured at runtime
    "manufacturingLocation":"MANUFACTURING LOCATION",
    "jurisdiction":         "JURISDICTION",
    "evidenceTier":         "EVIDENCE TIER",
    "evidenceScope":        "EVIDENCE SCOPE",
}
# Read but NEVER exported. Named so the refusal is explicit rather than an
# accident of omission.
SUPPLIER_LABELS_WITHHELD = {
    "CONTACT",           # personal contact data — phone numbers, email addresses
    "GPS COORDINATES",   # Most Local is frozen; no distance claim in E2
}

# ISSUE 005 PIECE E2.2 — A CORRECT LABEL CAN STILL CARRY PERSONAL DATA.
#
# The first real supplier artefact was refused by the validator:
#   recUnzSlV4tszVzg6.locality.irishPresence: personal contact data '+353 ...'
# The record was Ecohouse Building Systems, whose IRISH PRESENCE segment reads
# "Full — Irish premises with Eircode, Irish landline +353 ..., euro pricing
# ... business hours". The field, the label and the selection were all correct;
# the VALUE carried a landline as corroboration, and SUPPLIER_LABELS_WITHHELD
# only ever inspected a segment's HEAD.
#
# This pattern is byte-identical to SUPPLIER_PERSONAL in
# validate_garden_room_detail_evidence.py, deliberately: the producer must
# decline exactly what the gate would refuse, so the two cannot drift. The
# validator is untouched and remains the backstop.
SUPPLIER_PERSONAL_RE = re.compile(
    r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"      # email
    r"|(?:\+\d[\d ()-]{7,})"                                # international phone
)


def supplier_segment(text: str, label: str):
    """One labelled segment of a pipe-delimited Atlas locality record.

    `Headquarters` is `LABEL: value | LABEL: value | ...`. Splitting on the
    pipe and matching the label exactly is deterministic: no regex over prose,
    no inference about where a value starts or stops, and a malformed record
    yields nothing rather than something wrong.
    """
    if not text:
        return None
    for part in str(text).split("|"):
        part = part.strip()
        head, sep, value = part.partition(":")
        if not sep:
            continue
        head = head.strip().upper()
        if head in SUPPLIER_LABELS_WITHHELD:
            continue
        if head != label:
            continue
        value = value.strip()
        if not value:
            return None
        # An evidenced absence is a FACT and is kept: "None published" is a
        # finding. UNKNOWN is not, and is dropped rather than asserted.
        if value.lower() in ("unknown", "not established", "n/a", "tbc"):
            return None
        # ISSUE 005 PIECE E2.2 — the value-level refusal.
        #
        # The WHOLE segment goes, not the offending characters. Stripping the
        # number and keeping the remainder would mean deciding where the
        # evidence stops and the personal data starts, which is exactly the
        # derivation this programme refuses — and the brief forbids it by name.
        #
        # The cost is real and is accepted: Ecohouse, the organisation with the
        # strongest Irish evidence in the base, now exports irishPresence null
        # because its evidence cites a landline. A null here means "Atlas holds
        # this but it is not exportable in its present form", NOT "no Irish
        # presence". UNKNOWN is not FALSE.
        if SUPPLIER_PERSONAL_RE.search(value):
            return None
        return value
    return None

FEATURES_WANTED = {
    "irish availability":      "irishAvailability",
    "internal floor area":     "floorArea",
    "floor area":              "floorArea",
    "window glazing":          "glazing",
    "insulation status":       "insulation",
    "insulation":              "insulation",
    "year-round insulation":   "insulationRating",
    "construction system":     "construction",
    "construction material":   "construction",
    "external finish":         "cladding",
    "country of manufacture":  "countryOfManufacture",
    "design language":         "designLanguage",
    "installation model":      "installationModel",
    "measurement basis":       "measurementBasis",
    # ---- ISSUE 005 PIECE D3 — THE FIRST CONTROLLED WIDENING ----------------
    # Three categories, measured in Airtable and restricted to the 490 Garden
    # Rooms: 795 feature values between them. Each already exists in Atlas and
    # already follows the researcher convention C-C3 reads.
    #
    # "warranty status" is DELIBERATELY ABSENT. D1 established it as an older
    # overlapping vocabulary saying the same thing as "warranty" — Shomera
    # carries both, both stating 10 years structural and 20 on the roof. The
    # brief forbids exposing both, so only the current one is carried.
    "electrical included":     "electricalIncluded",
    "warranty":                "warranty",
    "external dimensions":     "externalDimensions",
}

# ── Irish availability vocabulary ────────────────────────────────────────────
# Deterministic, ordered, and deliberately asymmetric: the "unavailable"
# vocabulary must be an explicit statement that the product cannot be had in
# the Republic. Everything unrecognised is UNKNOWN.
IE_CONFIRMED = (
    "AVAILABLE ACROSS IRELAND",
    "AVAILABLE IN IRELAND",
    "AVAILABLE IN THE REPUBLIC OF IRELAND",
    # FIX 1. Atlas writes this WITHOUT the definite article, and the original
    # vocabulary carried it with. "AVAILABLE IN IRELAND" does not rescue the
    # case either: after "AVAILABLE IN " comes REPUBLIC, not IRELAND. One
    # missing word was resolving ~160 explicitly-positive products to UNKNOWN.
    "AVAILABLE IN REPUBLIC OF IRELAND",
    "REPUBLIC OF IRELAND CONFIRMED",
    "IRISH AVAILABILITY CONFIRMED",
    "SUPPLIES IRELAND",
)
IE_UNAVAILABLE = (
    "NOT AVAILABLE IN IRELAND",
    "NOT AVAILABLE IN THE REPUBLIC OF IRELAND",
    "DOES NOT SUPPLY IRELAND",
    "DOES NOT DELIVER TO IRELAND",
    "REPUBLIC OF IRELAND EXCLUDED",
    "NO IRISH AVAILABILITY",
)
IE_UNKNOWN = (
    "AVAILABILITY UNKNOWN",
    "REPUBLIC OF IRELAND UNCONFIRMED",
    "IRISH AVAILABILITY UNKNOWN",
    "UNCONFIRMED",
)

# FIX 2 — NO PUBLISHED IRISH ROUTE.
# The supplier's published delivery evidence covers the UK only. Atlas itself
# draws this distinction: on Quick-Garden it reasons that a supplier which
# "does not exclude Ireland, it simply says nothing about it" is UNCONFIRMED
# rather than restricted. UK ONLY goes further than silence — it is a
# published coverage boundary — but it still does not establish that an Irish
# homeowner could never obtain the product.
#
# So this is NOT a hard blocker and NOT `unavailable`. It resolves to UNKNOWN
# carrying an explicit signal, which keeps the product eligible while making
# High Confidence unreachable for it.
IE_NO_PUBLISHED_ROUTE = (
    "UK ONLY",
    "UNITED KINGDOM ONLY",
    "GB ONLY",
    "MAINLAND UK ONLY",
)

# A contradiction is only a hard blocker when Atlas has RECORDED one. These are
# the recorded markers; nothing is inferred from ordinary prose.
CONTRADICTION_MARKERS = (
    "UNRESOLVED CONTRADICTION",
    "CONTRADICTION UNRESOLVED",
    "DATA CONFLICT",
    "CONFLICTING EVIDENCE",
)
CONTRADICTION_STATUSES = ("Contradicted", "Conflict", "Disputed")

# ISSUE 005 PIECE E3a — THE CATEGORY-INTEGRITY EXCLUSION CONTRACT.
#
# CLOSED. Two literal phrases, measured across the complete Feature Value base
# as the only text that means "keep this out of garden-room recommendations"
# and never means anything else: 6 records, 3 products, 0 false positives.
#
# Adding a phrase here changes what PlotNua recommends. It is a founder
# decision with its own forensic, never a convenience.
CATEGORY_EXCLUSION_PHRASES = (
    "must be excluded from garden-room recommendations",
    "must never surface in a garden-room comparison",
)
# Deliberately NOT triggers — each has a MEASURED false-positive rate:
#   DO NOT RANK (391)  NOT A GARDEN ROOM (22)  CATEGORY INTEGRITY (7)
#   CATEGORY ISSUE     excluded from (65)      should never (1)
# Nor product name, product type, supplier, or category-adjacent vocabulary.

_WS = re.compile(r"\s+")


def _normalise(s: str) -> str:
    """Lower-case with runs of whitespace collapsed to one space.

    A line break or a double space inside the phrase must not defeat the
    match, and the phrase must read the same however it was typed. Nothing
    else is altered: no punctuation stripping, no stemming, no fuzziness.
    """
    return _WS.sub(" ", str(s or "")).strip().lower()


def category_exclusion(feat_rows):
    """The Atlas adjudication that this product must not be recommended.

    Returns (phrase, record_id) for the first Feature Value carrying one of
    the closed phrases, else None. Reads only `feat_rows` — the product's
    Feature Values, ALREADY LOADED for this product by main(); no extra
    Airtable call, and the canonical product id is the join.
    """
    for r in feat_rows or []:
        hay = _normalise(cell(r, "Value Text"))
        if not hay:
            continue
        for phrase in CATEGORY_EXCLUSION_PHRASES:
            if phrase in hay:
                return phrase, r.get("id")
    return None

PRICE_VERIFIED_STATUSES = ("Verified",)


def redact(msg) -> str:
    """Defence in depth on the one path a credential could conceivably travel.

    The token is only ever placed in an Authorization header, so no message
    built by this script contains it. But error text is assembled from
    exceptions raised by urllib, and an exception is somebody else's string.
    Anything that looks like a bearer token or an Airtable PAT is removed
    before it can reach a log, a workflow transcript or an artefact."""
    s = str(msg)
    s = re.sub(r"Bearer\s+\S+", "Bearer [REDACTED]", s)
    s = re.sub(r"\bpat[A-Za-z0-9._-]{10,}", "[REDACTED]", s)
    s = re.sub(r"\bkey[A-Za-z0-9]{14,}", "[REDACTED]", s)
    return s


def fail(msg):
    print(f"::error::{redact(msg)}", file=sys.stderr)
    print("Nothing was written.", file=sys.stderr)
    sys.exit(1)


# ── Airtable, read-only ──────────────────────────────────────────────────────
def fetch_all(token: str, table: str, fields: list) -> list:
    """Every record in one table, carrying the named fields. Raises on failure.

    Pagination is checked for stability: Airtable returns an offset until the
    set is exhausted, and a page that comes back empty while still offering an
    offset means the read is not to be trusted."""
    out, offset, pages = [], None, 0
    while True:
        q = [("pageSize", str(PAGE_SIZE))] + [("fields[]", f) for f in fields]
        if offset:
            q.append(("offset", offset))
        url = f"{API}/{BASE_ID}/{table}?{urllib.parse.urlencode(q)}"
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})

        for attempt in range(RETRIES):
            try:
                with urllib.request.urlopen(req, timeout=30) as r:
                    payload = json.loads(r.read().decode("utf-8"))
                break
            except urllib.error.HTTPError as e:
                if e.code in (429, 500, 502, 503, 504) and attempt < RETRIES - 1:
                    time.sleep(2 ** attempt)
                    continue
                raise RuntimeError(redact(f"{table}: HTTP {e.code} {e.reason}")) from e
            except Exception as e:
                if attempt < RETRIES - 1:
                    time.sleep(2 ** attempt)
                    continue
                raise RuntimeError(redact(f"{table}: {e}")) from e

        page = payload.get("records", [])
        offset = payload.get("offset")
        pages += 1
        if not page and offset:
            raise RuntimeError(f"{table}: empty page {pages} while still paginating")
        out.extend(page)
        if not offset:
            return out
        if pages > 500:
            raise RuntimeError(f"{table}: pagination did not terminate")
        time.sleep(0.25)


def cell(rec, field):
    v = rec.get("fields", {}).get(field)
    if isinstance(v, dict):
        return v.get("name")
    return v


def links(rec, field) -> list:
    v = rec.get("fields", {}).get(field) or []
    return [x.get("id") if isinstance(x, dict) else x for x in v]


def txt(v) -> str:
    return (v or "").strip() if isinstance(v, str) else ""


# ── the Match-compatible contract ───────────────────────────────────────────
# BRIDGE PIECE 1. These build the flat view your-plot.html reads. They add;
# they never replace. Every one of them returns None rather than a guess.

# Units Atlas may record a floor area in. Only these are square metres, and a
# number carrying any other unit is NOT emitted as floorAreaM2 — publishing a
# cm² figure as m² would be a wrong number, which is worse than no number.
M2_UNITS = ("m2", "m²", "sqm", "sq m", "square metres", "square meters")


def feature_text(features: dict, key: str):
    v = (features or {}).get(key)
    return (v or {}).get("text") or None


def feature_m2(features: dict, key: str):
    """A floor area in square metres, or None. Unit-checked, never assumed."""
    v = (features or {}).get(key) or {}
    n = v.get("number")
    if not isinstance(n, (int, float)) or isinstance(n, bool):
        return None
    unit = txt(v.get("unit")).lower()
    if unit and unit not in M2_UNITS:
        return None                      # a real number in the wrong unit
    return n


def match_price(price_rec):
    """(numeric price or None, currency, basis).

    Base Price first, then Price From. Structured evidence only: no prose is
    parsed, nothing is inferred, and an unknown price is None — never 0."""
    if not price_rec:
        return None, None, None
    for field in ("Base Price", "Price From"):
        v = cell(price_rec, field)
        if isinstance(v, (int, float)) and not isinstance(v, bool):
            return v, cell(price_rec, "Currency"), cell(price_rec, "Status")
    return None, cell(price_rec, "Currency"), cell(price_rec, "Status")


def match_irish_state(ie_state: str):
    """The ruled mapping. no-published-irish-route is NOT unavailable and is
    handled by its own boolean, so it never reaches this function as "No"."""
    if ie_state == "confirmed":
        return "Yes"
    if ie_state == "unavailable":
        return "No"
    return None                          # unknown stays unknown


# ── qualification ────────────────────────────────────────────────────────────
def classify_irish_availability(feat_rows: list) -> tuple:
    """(state, basis, scope, classified, no_route) for Irish availability.

    state is confirmed | unknown | unavailable. `no_route` marks the
    no-published-irish-route case, which is a kind of UNKNOWN, never a kind of
    unavailable. `classified` is False when a lead phrase was present but
    matched no vocabulary — that product still resolves to UNKNOWN, and the
    caller counts it so the parser's blind spots stay visible.

    ORDER OF EVIDENCE, AND WHY IT CHANGED.

    The first version read Confirmation State first and returned immediately
    on a legacy `No`. That produced the incoherence the diagnostic found: six
    products hard-excluded on a legacy checkbox while ~48 carrying the same
    UK-ONLY prose stayed eligible, because their checkbox was blank.

    A legacy `No` is now a CANDIDATE for unavailable, not a verdict. It is
    honoured only when the accompanying text explicitly establishes that the
    Republic cannot be served. Where the text says only that coverage is UK
    ONLY, the product is UNKNOWN + no-published-irish-route. Where there is no
    text at all, a bare legacy `No` is not explicit evidence of anything and
    resolves to UNKNOWN.

    UNAVAILABLE is reserved for evidence that says so in terms.
    """
    best = ("unknown", "no irish-availability evidence recorded", None)
    classified = True
    no_route = False
    legacy_no = None                      # a bare `No`, pending corroboration

    for row in feat_rows:
        scope = cell(row, "Evidence Scope")
        conf = txt(cell(row, "Confirmation State"))
        body = txt(cell(row, "Value Text"))
        head = body.upper()

        # A positive Confirmation State is still decisive: it is an explicit
        # statement, and nothing in the ruling weakens it.
        if conf and conf.lower().startswith("yes"):
            return ("confirmed", f"Confirmation State: {conf}", scope, True, False)

        # Text is now read before a negative Confirmation State is honoured.
        if body:
            if any(head.startswith(p) for p in IE_UNAVAILABLE):
                return ("unavailable", body[:200], scope, True, False)
            if any(head.startswith(p) for p in IE_CONFIRMED):
                return ("confirmed", body[:200], scope, True, False)
            if any(head.startswith(p) for p in IE_NO_PUBLISHED_ROUTE):
                no_route = True
                best = ("unknown", body[:200], scope)
                continue
            if any(head.startswith(p) for p in IE_UNKNOWN):
                best = ("unknown", body[:200], scope)
                continue
            classified = False
            best = ("unknown", body[:200], scope)
            continue

        if conf:
            c = conf.lower()
            if c == "no":
                legacy_no = (f"Confirmation State: {conf} (no accompanying evidence text)", scope)
            elif c == "unknown":
                best = ("unknown", f"Confirmation State: {conf}", scope)

    # A legacy `No` that nothing corroborates is not explicit evidence of
    # unavailability. It lowers nothing and excludes nothing.
    if legacy_no and best[1] == "no irish-availability evidence recorded":
        best = ("unknown", legacy_no[0], legacy_no[1])

    return best + (classified, no_route)


def usable_price(price_rows: list) -> tuple:
    """(state, record) — verified | present-unverified | missing."""
    if not price_rows:
        return ("missing", None)
    primary = [r for r in price_rows if cell(r, "Primary Price")] or price_rows
    verified = [r for r in primary if cell(r, "Status") in PRICE_VERIFIED_STATUSES]
    pick = (verified or primary)[0]
    has_number = any(cell(pick, f) is not None
                     for f in ("Base Price", "Price From", "Price To"))
    if not has_number:
        return ("missing", pick)
    return ("verified" if verified else "present-unverified", pick)


def has_contradiction(product, feat_rows, price_rows) -> str:
    status = txt(cell(product, "Verification Status"))
    if status in CONTRADICTION_STATUSES:
        return f"Verification Status = {status}"
    blobs = [txt(cell(product, "Notes")), txt(cell(product, "Description"))]
    blobs += [txt(cell(r, "Value Text")) for r in feat_rows]
    blobs += [txt(cell(r, "Notes")) for r in price_rows]
    for b in blobs:
        up = b.upper()
        for m in CONTRADICTION_MARKERS:
            if m in up:
                return f"recorded marker: {m}"
    return ""


def qualify(product, orgs, price_rows, avail_rows, feat_rows,
            all_feat_rows=None) -> dict:
    """Deterministic. Same inputs, same output, every run.

    ISSUE 005 PIECE E3a — A NAMING TRAP, RECORDED SO IT CANNOT BITE AGAIN.
    `feat_rows` is NOT every Feature Value for the product. main() passes
    `ie_rows` — the IRISH AVAILABILITY subset — and blockers A-D depend on
    exactly that. Blocker E needs the whole evidence set, so it takes its own
    parameter and A-D keep the input they have always had.
    """
    name = txt(cell(product, "Product Name"))
    org_ids = links(product, "Organisation")
    org_names = [orgs.get(i, {}).get("name", "") for i in org_ids]
    url = txt(cell(product, "Product URL"))
    sources_text = txt(cell(product, "    Sources"))
    ie_state, ie_basis, ie_scope, ie_classified, ie_no_route = classify_irish_availability(feat_rows)
    price_state, price_rec = usable_price(price_rows)
    contradiction = has_contradiction(product, feat_rows, price_rows)

    # ---- hard blockers: evidence of a reason, never absence of evidence ----
    hard = []
    if not org_ids:
        hard.append({"code": "A", "reason": "No identifiable Organisation attribution",
                     "sourceFields": ["Organisation"]})
    if ie_state == "unavailable":
        hard.append({"code": "B", "reason": "Evidence confirms unavailable in the Republic of Ireland",
                     "sourceFields": ["Product Feature Values: Irish Availability"],
                     "evidence": ie_basis})
    if contradiction:
        hard.append({"code": "C", "reason": "Recorded unresolved contradiction",
                     "sourceFields": ["Verification Status", "Notes"],
                     "evidence": contradiction})
    if not name or txt(cell(product, "Product Category")) != GARDEN_ROOMS:
        hard.append({"code": "D", "reason": "Cannot be reliably identified as a Garden Room product",
                     "sourceFields": ["Product Name", "Product Category"]})
    # ---- ISSUE 005 PIECE E3a — BLOCKER E -----------------------------------
    # Blocker D tests the Airtable CATEGORY FIELD. These products are filed
    # under Garden Rooms, so D passes them — while the research evidence for
    # the very same product says they must be excluded. D is about how a record
    # is filed; E is about what Atlas has decided.
    adjudication = category_exclusion(
        all_feat_rows if all_feat_rows is not None else feat_rows)
    if adjudication:
        _phrase, _rec_id = adjudication
        hard.append({"code": "E",
                     "reason": "Atlas has explicitly adjudicated that this product "
                               "must not participate in Garden Room recommendations",
                     "sourceFields": ["Product Feature Values: category adjudication"],
                     "evidence": _phrase,
                     "evidenceRecordId": _rec_id})

    # ---- evidence signals ----
    scopes = [cell(r, "Evidence Scope") for r in feat_rows if cell(r, "Evidence Scope")]
    price_scope = cell(price_rec, "Evidence Scope") if price_rec else None
    if url:
        source_level = "product-level"
    elif sources_text or price_scope == "Product-Specific":
        source_level = "supplier-level"
    elif scopes:
        source_level = "range-level"
    else:
        source_level = "missing"

    signals = {
        "irishAvailability": ie_state,
        "irishAvailabilityBasis": ie_basis,
        "irishAvailabilityScope": ie_scope,
        "irishAvailabilityClassified": ie_classified,
        # FIX 2 — a kind of UNKNOWN, never a kind of unavailable.
        "noPublishedIrishRoute": ie_no_route,
        "price": price_state,
        "source": source_level,
        "supplierAttribution": "confirmed" if org_ids else "unresolved",
        "manufacturerAttribution": "confirmed" if any(
            "country of manufacture" in txt(cell(r, "Product Feature Value Name")).lower()
            for r in feat_rows) else "unknown",
        "productUrl": "present" if url else "missing",
        "contradiction": "recorded" if contradiction else "none",
        "productEvidenceCompleteness": txt(cell(product, "Atlas Product Certification Audit v1")) or "not assessed",
        "featureValueCount": len(feat_rows),
        "pricingRecordCount": len(price_rows),
        "availabilityRecordCount": len(avail_rows),
    }

    if hard:
        return {"status": "EXCLUDED — HARD BLOCKER", "confidenceTier": None,
                "reasons": [], "caveats": [], "hardBlockers": hard,
                "evidenceSignals": signals}

    # ---- caveats: material but never blocking ----
    caveats, reasons = [], []
    if ie_state == "unknown" and ie_no_route:
        caveats.append("Irish availability not established \u2014 the supplier's published "
                       "delivery information currently covers the UK only.")
    elif ie_state == "unknown":
        caveats.append("Irish availability is not yet confirmed. Nothing establishes it is unavailable.")
    else:
        reasons.append("Irish availability is confirmed by recorded evidence.")
    if price_state == "present-unverified":
        caveats.append("A published price is recorded but has not been verified.")
    elif price_state == "missing":
        caveats.append("No usable price is recorded.")
    else:
        reasons.append("A verified price is recorded.")
    if source_level == "missing":
        caveats.append("No product-level or supplier-level source is recorded.")
    elif source_level != "product-level":
        caveats.append(f"Evidence reaches {source_level} rather than this exact product.")
    else:
        reasons.append("A product-level source is recorded.")
    if not url:
        caveats.append("Product URL is missing; product identity is established by other evidence.")
    if any("measurement basis" in txt(cell(r, "Product Feature Value Name")).lower()
           and not txt(cell(r, "Value Text")) for r in feat_rows):
        caveats.append("Measurement basis is recorded but unresolved.")
    if org_ids:
        reasons.append(f"Supplier attribution is confirmed: {', '.join(n for n in org_names if n)}.")

    # ---- tier ----
    strong_identity = bool(org_ids and name)
    if (ie_state == "confirmed" and price_state in ("verified", "present-unverified")
            and source_level in ("product-level", "supplier-level") and strong_identity):
        tier, status = "HIGH_CONFIDENCE", "ELIGIBLE — HIGH CONFIDENCE"
    elif source_level == "missing":
        # FIX 3 — LIMITED EVIDENCE means the product evidence itself is weak,
        # not that a price is absent. Price uncertainty and evidence
        # confidence are separate concepts: a well-sourced product with no
        # published price is WITH CAVEAT, and says so.
        #
        # The remaining evidence-based distinction available from the current
        # structured data is whether Atlas holds ANY usable source for the
        # product at any scope — no Product URL, no Sources text, no
        # product-specific price evidence and no recorded evidence scope. If
        # that population turns out to be empty, it stays empty. A tier is not
        # filled to make a distribution look balanced.
        tier, status = "LIMITED_EVIDENCE", "ELIGIBLE — LIMITED EVIDENCE"
    else:
        tier, status = "WITH_CAVEAT", "ELIGIBLE — WITH CAVEAT"

    return {"status": status, "confidenceTier": tier, "reasons": reasons,
            "caveats": caveats, "hardBlockers": [], "evidenceSignals": signals}


# ── sanity gates ─────────────────────────────────────────────────────────────
def gates(products, emitted, excluded, source_count):
    if source_count == 0:
        fail("Garden Room source count is 0. Treated as a failure, never a result — "
             "most likely the 'Garden Rooms' choice or 'Product Category' was renamed.")
    ids = [p["id"] for p in products]
    if len(ids) != len(set(ids)):
        dupes = {i for i in ids if ids.count(i) > 1}
        fail(f"Duplicate Airtable Product IDs in the source read: {sorted(dupes)[:10]}")
    if len(emitted) + len(excluded) != source_count:
        fail(f"Totals do not reconcile: {len(emitted)} eligible + {len(excluded)} excluded "
             f"!= {source_count} source Garden Rooms.")
    for e in excluded:
        if not e["qualification"]["hardBlockers"]:
            fail(f"Excluded product {e['productId']} has no recorded exclusion reason.")
    for p in emitted:
        q = p["qualification"]
        if q["hardBlockers"]:
            fail(f"Eligible product {p['productId']} carries a hard blocker.")
        if q["evidenceSignals"]["irishAvailability"] == "unavailable":
            fail(f"Product {p['productId']} is confirmed unavailable yet classified eligible.")
        if q["confidenceTier"] not in ("HIGH_CONFIDENCE", "WITH_CAVEAT", "LIMITED_EVIDENCE"):
            fail(f"Product {p['productId']} has an unrecognised confidence tier.")
    for rec in emitted + excluded:
        for k in ("productId", "productName", "organisation", "qualification"):
            if k not in rec:
                fail(f"Output record is malformed: missing {k}.")


# ── main ─────────────────────────────────────────────────────────────────────
def main():
    ap = argparse.ArgumentParser(description="Garden Room Match Qualification v1 (dry run).")
    ap.add_argument("--out-dir", required=True,
                    help="Directory for the dry-run artefacts. Never a production path.")
    ap.add_argument("--snapshot", default=None,
                    help="Read a local JSON snapshot instead of Airtable (offline testing only).")
    ap.add_argument("--write-snapshot", default=None,
                    help="Save the raw Airtable read to this path for reproducibility.")
    ap.add_argument("--allow-production-write", action="store_true",
                    help="Refused. Present so that its absence is explicit, not implied.")
    args = ap.parse_args()

    if args.allow_production_write:
        fail("This phase is dry-run only. Production write is not implemented.")

    out = Path(args.out_dir)
    for forbidden in ("recommendation-universe-v1.json", "atlas-match-pool.json",
                      "atlas-recognition-pool.json", "your-plot.html"):
        if (out / forbidden).exists():
            fail(f"Refusing to write into a directory holding {forbidden}.")
    out.mkdir(parents=True, exist_ok=True)

    if args.snapshot:
        raw = json.loads(Path(args.snapshot).read_text(encoding="utf-8"))
        print(f"Offline snapshot: {args.snapshot}")
    else:
        token = os.environ.get("AIRTABLE_TOKEN")
        if not token:
            fail("AIRTABLE_TOKEN is not set. This script reads it from the environment "
                 "only, and never accepts a credential by any other route.")
        print("Reading Atlas (read-only)…")
        try:
            raw = {
                "products":  fetch_all(token, T_PRODUCTS, PRODUCT_FIELDS),
                "pricing":   fetch_all(token, T_PRICING, PRICING_FIELDS),
                "availability": fetch_all(token, T_AVAIL, AVAIL_FIELDS),
                "featureValues": fetch_all(token, T_FEATVALS, FEATVAL_FIELDS),
                "features":  fetch_all(token, T_FEATURES, FEATURE_FIELDS),
                "organisations": fetch_all(token, T_ORGS, ["Organisation Name", "Organisation Type", "Website",
                                                       "Headquarters", "Sources"]),
            }
        except Exception as e:
            fail(f"Atlas read failed: {e}")
        if args.write_snapshot:
            Path(args.write_snapshot).write_text(json.dumps(raw), encoding="utf-8")

    orgs = {r["id"]: {"name": txt(cell(r, "Organisation Name"))} for r in raw["organisations"]}
    features = {r["id"]: txt(cell(r, "Feature Name")) for r in raw["features"]}
    ie_feature_ids = {fid for fid, n in features.items() if n.lower() == "irish availability"}

    garden = [p for p in raw["products"]
              if txt(cell(p, "Product Category")) == GARDEN_ROOMS]
    source_count = len(garden)
    print(f"  Garden Rooms read: {source_count}")

    by_product = {"pricing": {}, "availability": {}, "featureValues": {}}
    for key, rows in (("pricing", raw["pricing"]), ("availability", raw["availability"]),
                      ("featureValues", raw["featureValues"])):
        for r in rows:
            for pid in links(r, "Product"):
                by_product[key].setdefault(pid, []).append(r)

    emitted, excluded = [], []
    # ISSUE 005 PIECE D4b — long-form evidence, keyed by canonical product id.
    detail_products = {}
    unclassified_ie = 0
    no_route_count = 0
    for p in sorted(garden, key=lambda r: (txt(cell(r, "Product Name")), r["id"])):
        pid = p["id"]
        fv = by_product["featureValues"].get(pid, [])
        ie_rows = [r for r in fv if set(links(r, "Feature")) & ie_feature_ids] or [
            r for r in fv if "irish availability" in txt(cell(r, "Product Feature Value Name")).lower()]
        q = qualify(p, orgs, by_product["pricing"].get(pid, []),
                    by_product["availability"].get(pid, []), ie_rows,
                    all_feat_rows=fv)   # E3a: fv is EVERY Feature Value for pid
        if not q["evidenceSignals"]["irishAvailabilityClassified"]:
            unclassified_ie += 1
        if q["evidenceSignals"].get("noPublishedIrishRoute"):
            no_route_count += 1

        org_names = [orgs.get(i, {}).get("name", "") for i in links(p, "Organisation")]
        rec = {
            # BRIDGE PIECE 1 — the Match contract. `id` and `name` are the
            # canonical Airtable record id and Product Name, and they sit on
            # EVERY record including excluded ones, so the exclusions audit is
            # identifiable by the same key Match, Compare, My Plot and Product
            # Detail all use.
            "id": pid,
            "name": txt(cell(p, "Product Name")),
            "organisation": next((n for n in org_names if n), None),
            "productId": pid,
            "productCode": txt(cell(p, "Product Code")),
            "productName": txt(cell(p, "Product Name")),
            "productType": txt(cell(p, "Product Type")),
            "productCategory": txt(cell(p, "Product Category")),
            # The structured evidence is preserved, moved to its own key so the
            # flat Match `organisation` above can be the display string the
            # website reads. Nothing is lost.
            "organisationEvidence": [{"id": i, "name": orgs.get(i, {}).get("name", "")}
                                     for i in links(p, "Organisation")],
            "productUrl": txt(cell(p, "Product URL")) or None,
            "verificationStatus": txt(cell(p, "Verification Status")) or None,
            "qualification": q,
        }
        if q["hardBlockers"]:
            excluded.append(rec)
        else:
            price_rows = by_product["pricing"].get(pid, [])
            _, pick = usable_price(price_rows)
            # Renamed so the flat numeric `price` Match reads can take that key.
            # The structured evidence is preserved in full, not summarised away.
            rec["priceEvidence"] = None if not pick else {
                "base": cell(pick, "Base Price"), "from": cell(pick, "Price From"),
                "to": cell(pick, "Price To"), "currency": cell(pick, "Currency"),
                "priceType": cell(pick, "Price Type"), "status": cell(pick, "Status"),
                "includesVat": cell(pick, "Price Includes VAT"),
                "evidenceScope": cell(pick, "Evidence Scope"),
            }
            # ---- ISSUE 005 PIECE D2 — THE PIPE STOPS LEAKING ---------------
            # `if key not in carried` discarded every Atlas Feature Value after
            # the first for any key. D1 measured 396 records lost that way
            # across the 490, before any catalogue widening.
            #
            # features[key] KEEPS ITS EXACT SHAPE. Every consumer reads a single
            # object — atlasFeatureRead() and pnVatPosition() in your-plot.html,
            # feature_text() and feature_m2() here, and the i5b/i5c guards — and
            # all of them read .text/.number/.unit. An array would make .text
            # undefined and silently empty the whole C-C3 evidence architecture
            # instead of failing loudly, so the array was rejected on evidence.
            #
            # The complete set is carried alongside, in `records`, and ONLY where
            # Atlas actually holds more than one. Single-record keys are
            # unchanged apart from truth metadata Atlas genuinely has.
            #
            # PRIMARY SELECTION IS UNCHANGED, DELIBERATELY. Nine Garden Rooms
            # have a numeric "Floor Area" record contradicting an "Internal
            # Floor Area" record that says NO AREA PUBLISHED, NOTHING ESTIMATED.
            # Preferring the number would hand each of them an area, move
            # ranking, and overrule a record that explicitly refuses to
            # estimate. D2 records the conflict and leaves the decision to the
            # founder; it does not quietly pick the prettier answer.
            #
            # `records` order is ARRIVAL order and carries NO precedence. Each
            # entry carries its own evidenceScope, confirmationState and status
            # so a consumer can adjudicate on evidence rather than on position.
            carried = {}
            for r in by_product["featureValues"].get(pid, []):
                fname = next((features.get(i, "") for i in links(r, "Feature")), "")
                key = FEATURES_WANTED.get(fname.lower())
                if not key:
                    continue
                one = {"text": txt(cell(r, "Value Text")) or None,
                       "number": cell(r, "Value Number"),
                       "unit": cell(r, "Unit"),
                       "evidenceScope": cell(r, "Evidence Scope")}
                # Fetched by FEATVAL_FIELDS and previously thrown away. Present
                # only where Atlas holds a value, so absent keeps meaning
                # "Atlas holds nothing here" rather than "Atlas holds nothing".
                conf = cell(r, "Confirmation State")
                stat = cell(r, "Status")
                if conf: one["confirmationState"] = conf
                if stat: one["status"] = stat
                one["feature"] = fname or None
                if key not in carried:
                    carried[key] = dict(one)          # primary: selection unchanged
                    carried[key]["records"] = [one]
                else:
                    carried[key]["records"].append(one)

            # A single record needs no set, and naming its Atlas feature is only
            # useful where two aliases competed. Keeping both off the 2,446
            # single-record keys is what holds the payload growth down.
            for _v in carried.values():
                if len(_v["records"]) < 2:
                    _v.pop("records")
                    _v.pop("feature", None)
            rec["features"] = carried

            # ---- ISSUE 005 PIECE D4b — the same carry, into the detail file --
            # Identical D2 semantics: nothing is discarded, colliding evidence
            # is preserved in records[], and truth metadata is kept only where
            # Atlas holds it. This dict never touches `rec`, so no long-form
            # prose can reach the core Match universe.
            detail = {}
            for r in by_product["featureValues"].get(pid, []):
                fname = next((features.get(i, "") for i in links(r, "Feature")), "")
                key = DETAIL_FEATURES_WANTED.get(fname.lower())
                if not key:
                    continue
                one = {"text": txt(cell(r, "Value Text")) or None,
                       "evidenceScope": cell(r, "Evidence Scope")}
                conf = cell(r, "Confirmation State")
                stat = cell(r, "Status")
                if conf: one["confirmationState"] = conf
                if stat: one["status"] = stat
                one["feature"] = fname or None
                if key not in detail:
                    detail[key] = dict(one)
                    detail[key]["records"] = [one]
                else:
                    detail[key]["records"].append(one)
            for _v in detail.values():
                if len(_v["records"]) < 2:
                    _v.pop("records")
                    _v.pop("feature", None)
            # A product with no long-form evidence is simply absent from the
            # detail artefact. Absent is not an error and not an empty entry.
            # ---- ISSUE 005 PIECE E2 — PROVENANCE ---------------------------
            # `"    Sources"` — the leading spaces are Airtable's field name,
            # not a typo — has been READ by this generator since Piece 5 and
            # never emitted. 363 of 490 products carry it.
            #
            # It is exported as the text Atlas holds, at PRODUCT level, because
            # that is the only attribution the schema supports. No URL parsing,
            # no per-field attribution, no invented relationship between a
            # source and a particular Feature Value.
            src = txt(cell(p, "    Sources"))
            if src:
                detail_products.setdefault(pid, {})[DETAIL_PROVENANCE_KEY] = {
                    "text": src, "evidenceScope": None}

            if detail:
                detail_products.setdefault(pid, {}).update(detail)

            # ---- BRIDGE PIECE 1 — the flat Match view -----------------------
            # Built from the evidence already gathered above. Added beside the
            # qualification block, never instead of it.
            sig = q["evidenceSignals"]
            num, cur, basis = match_price(pick)
            avail_rows_p = by_product["availability"].get(pid, [])
            rec.update({
                "price": num,                       # numeric or null, never 0-for-unknown
                "currency": cur or ("EUR" if num is not None else None),
                "priceBasis": basis,
                "floorAreaM2": feature_m2(carried, "floorArea"),
                "glazing": feature_text(carried, "glazing"),
                "insulation": feature_text(carried, "insulation"),
                "manufactureCountry": feature_text(carried, "countryOfManufacture"),
                "designLanguage": feature_text(carried, "designLanguage"),
                "irishAvailabilityConfirmationState": match_irish_state(sig["irishAvailability"]),
                # your-plot.html's normalizePoolProduct derives the confirmation
                # state from a BOOLEAN `irishAvailability`, not from the string
                # above — measured, not assumed. So the boolean is emitted too,
                # carrying exactly the ruled mapping: confirmed -> true,
                # unavailable -> false, unknown -> absent (never false). The
                # page therefore needs no change to read this contract.
                "irishAvailability": (True if sig["irishAvailability"] == "confirmed"
                                      else False if sig["irishAvailability"] == "unavailable"
                                      else None),
                "availabilityStatus": next(
                    (txt(cell(r, "Availability")) for r in avail_rows_p
                     if txt(cell(r, "Availability"))), None),
                "noPublishedIrishRoute": bool(sig.get("noPublishedIrishRoute")),
                "qualificationTier": q["confidenceTier"],
                "qualificationCaveats": q["caveats"],
            })
            emitted.append(rec)

    gates(garden, emitted, excluded, source_count)

    tiers = {t: sum(1 for e in emitted if e["qualification"]["confidenceTier"] == t)
             for t in ("HIGH_CONFIDENCE", "WITH_CAVEAT", "LIMITED_EVIDENCE")}
    ie = {s: sum(1 for e in emitted + excluded
                 if e["qualification"]["evidenceSignals"]["irishAvailability"] == s)
          for s in ("confirmed", "unknown", "unavailable")}
    blockers = {}
    for e in excluded:
        for b in e["qualification"]["hardBlockers"]:
            blockers[b["code"]] = blockers.get(b["code"], 0) + 1

    # ---- ISSUE 005 PIECE E3a — name every category-adjudicated exclusion ----
    # Operator diagnostics, printed to the run log and never sent to a
    # homeowner. A silent exclusion is indistinguishable from a bug, so each
    # one states the product, the supplier, the phrase Atlas used and the
    # record that authorises it.
    _cat_excluded = [e for e in excluded
                     if any(b["code"] == "E" for b in e["qualification"]["hardBlockers"])]
    print(f"\n  Category-integrity exclusions (Blocker E): {len(_cat_excluded)}")
    for e in _cat_excluded:
        _b = [b for b in e["qualification"]["hardBlockers"] if b["code"] == "E"][0]
        print(f"    {e['productId']}  {e.get('productName') or '?'}"
              f"  [{e.get('organisation') or 'no organisation'}]")
        print(f"      authorised by {_b.get('evidenceRecordId')}: \"{_b.get('evidence')}\"")

    payload = {
        "schema": SCHEMA,
        "version": VERSION,
        "generated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "sourceBase": BASE_ID,
        "qualificationRuleVersion": RULE_VERSION,
        "dryRun": True,
        "sourceGardenRoomCount": source_count,
        "eligibleCount": len(emitted),
        "highConfidenceCount": tiers["HIGH_CONFIDENCE"],
        "withCaveatCount": tiers["WITH_CAVEAT"],
        "limitedEvidenceCount": tiers["LIMITED_EVIDENCE"],
        "excludedCount": len(excluded),
        "exclusionSummaryByReason": blockers,
        "confirmedIrishAvailabilityCount": ie["confirmed"],
        "unknownIrishAvailabilityCount": ie["unknown"],
        "confirmedUnavailableCount": ie["unavailable"],
        "unclassifiedIrishAvailabilityCount": unclassified_ie,
        "noPublishedIrishRouteCount": no_route_count,
        "missingPriceCount": sum(1 for e in emitted
                                 if e["qualification"]["evidenceSignals"]["price"] == "missing"),
        "missingProductUrlCount": sum(1 for e in emitted + excluded
                                      if not e.get("productUrl")),
        "products": emitted,
    }
    audit = {"schema": SCHEMA + ".exclusions", "generated": payload["generated"],
             "qualificationRuleVersion": RULE_VERSION,
             "excludedCount": len(excluded), "excluded": excluded}

    (out / "garden-room-recommendation-universe-v1.json").write_text(
        json.dumps(payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")
    (out / "garden-room-exclusions-v1.json").write_text(
        json.dumps(audit, indent=2) + "\n", encoding="utf-8")

    # ---- ISSUE 005 PIECE D4b — THE DETAIL EVIDENCE ARTEFACT -----------------
    # Keyed by canonical Airtable product id, which is the ONLY join. No price,
    # no ranking, no qualification, no organisation — nothing that would make
    # this a second copy of the product.
    detail_payload = {
        "schema": SCHEMA + ".detail",
        "version": VERSION,
        "generated": payload["generated"],
        "sourceBase": BASE_ID,
        # ISSUE 005 PIECE E2.1 — the provenance key is a CATEGORY IN THE DATA,
        # so it must be declared here too. E2 added `sources` to every product
        # entry but left this declaration derived from DETAIL_FEATURES_WANTED
        # alone, and the validator correctly refused the file:
        #   "category present in the data but not declared: 'sources'"
        # Publication is all-or-none, so that single undeclared key would have
        # blocked the whole 06:15 run even after the NameError was fixed. This
        # is the same expression the partition writer already uses below.
        "categories": sorted(set(DETAIL_FEATURES_WANTED.values())) + [DETAIL_PROVENANCE_KEY],
        "productCount": len(detail_products),
        "recordCounts": {k: sum(len(v[k].get("records", [None]))
                                for v in detail_products.values() if k in v)
                         for k in sorted(set(DETAIL_FEATURES_WANTED.values()))
                                  + [DETAIL_PROVENANCE_KEY]},
        "products": detail_products,
    }
    (out / "garden-room-detail-evidence-v1.json").write_text(
        json.dumps(detail_payload, indent=2, sort_keys=False) + "\n", encoding="utf-8")

    # ---- ISSUE 005 PIECE E2 — ONE PARTITION PER CATEGORY --------------------
    # Same shape as the combined file, one category each, so the validator and
    # the runtime reader need no special case: a partition IS a detail artefact
    # that happens to declare one category.
    #
    # The combined file above is still written, byte-compatible with D4b, so
    # the currently deployed page keeps working while the runtime moves over.
    # ---- ISSUE 005 PIECE E2a — SUPPLIER EVIDENCE ---------------------------
    # Only organisations actually attributed to an exported Garden Room. The
    # other suppliers in the table are not this artefact's business.
    _linked_orgs = set()
    for _p in garden:
        for _oid in links(_p, "Organisation"):
            _linked_orgs.add(_oid)

    supplier_evidence = {}
    for _r in raw["organisations"]:
        _oid = _r["id"]
        if _oid not in _linked_orgs:
            continue
        _hq = txt(cell(_r, "Headquarters"))
        _rec = {}
        for _key, _label in SUPPLIER_LABELS.items():
            _v = supplier_segment(_hq, _label)
            if _v:
                _rec[_key] = _v
        _src = txt(cell(_r, "Sources"))
        if _src:
            _rec["sources"] = _src
        if not _rec:
            continue
        # `locality`, NOT `irish`. marketEligibility reads `.irish` and
        # getEligibleAtlasPool filters the pool on it; an empty `.irish` would
        # change the sentence a homeowner reads from "Atlas has not
        # established" to "Atlas read the maker's delivery information", which
        # for these suppliers is not true. Results Eligibility v1 is frozen.
        supplier_evidence[_oid] = {
            "name": orgs.get(_oid, {}).get("name", ""),
            "locality": _rec,
        }

    # Shaped as a PARTITION, not a special case: same keys, same index entry,
    # same validator run, same atomic publication. Only its per-record shape
    # differs, and that is what the validator dispatches on.
    supplier_doc = {
        "schema": SCHEMA + ".detail",
        "version": VERSION,
        "generated": payload["generated"],
        "categories": [DETAIL_SUPPLIER_KEY],
        "productCount": len(supplier_evidence),
        "products": supplier_evidence,
    }
    _sup_file = (DETAIL_PARTITION_PREFIX + DETAIL_SUPPLIER_KEY
                 + DETAIL_PARTITION_SUFFIX)
    _sup_raw = json.dumps(supplier_doc, indent=2, sort_keys=False) + "\n"
    (out / _sup_file).write_text(_sup_raw, encoding="utf-8")
    print(f"  supplier evidence: {len(supplier_evidence)} organisations, "
          f"{len(_sup_raw)} bytes")

    detail_index = {
        "schema": SCHEMA + ".detail.index",
        "version": VERSION,
        "generated": payload["generated"],
        "partitions": [],
    }
    _all_categories = sorted(set(DETAIL_FEATURES_WANTED.values())) + [DETAIL_PROVENANCE_KEY]
    for _cat in _all_categories:
        _prods = {pid: {_cat: rec[_cat]} for pid, rec in detail_products.items() if _cat in rec}
        if not _prods:
            continue
        _part = {
            "schema": SCHEMA + ".detail",
            "version": VERSION,
            "generated": payload["generated"],
            "sourceBase": BASE_ID,
            "categories": [_cat],
            "productCount": len(_prods),
            "recordCounts": {_cat: sum(len(v[_cat].get("records", [None])) for v in _prods.values())},
            "products": _prods,
        }
        _name = DETAIL_PARTITION_PREFIX + _cat.lower() + DETAIL_PARTITION_SUFFIX
        _text = json.dumps(_part, indent=2, sort_keys=False) + "\n"
        (out / _name).write_text(_text, encoding="utf-8")
        detail_index["partitions"].append({
            "category": _cat, "file": _name,
            "productCount": _prods and len(_prods) or 0,
            "recordCount": _part["recordCounts"][_cat],
            "rawBytes": len(_text.encode("utf-8")),
        })
    # ISSUE 005 PIECE E2a — the supplier partition is a first-class partition:
    # same shape, same validator, same atomic publication. It is declared here
    # so the runtime learns of it the same way it learns of every other, and
    # so it CANNOT be published without being validated.
    detail_index["partitions"].append({
        "category": DETAIL_SUPPLIER_KEY,
        "file": _sup_file,
        "productCount": len(supplier_evidence),
        "recordCount": sum(len(v["locality"]) for v in supplier_evidence.values()),
        "rawBytes": len(_sup_raw),
    })

    (out / DETAIL_INDEX_FILE).write_text(
        json.dumps(detail_index, indent=2, sort_keys=False) + "\n", encoding="utf-8")

    lines = [
        "GARDEN ROOM MATCH QUALIFICATION v1 — DRY RUN",
        f"generated {payload['generated']}   rule {RULE_VERSION}",
        "",
        f"  Garden Rooms read            {source_count:>5}",
        f"  ELIGIBLE                     {len(emitted):>5}",
        f"    High Confidence            {tiers['HIGH_CONFIDENCE']:>5}",
        f"    With Caveat                {tiers['WITH_CAVEAT']:>5}",
        f"    Limited Evidence           {tiers['LIMITED_EVIDENCE']:>5}",
        f"  EXCLUDED — hard blocker      {len(excluded):>5}",
        "",
        "  Irish availability",
        f"    confirmed                  {ie['confirmed']:>5}",
        f"    unknown                    {ie['unknown']:>5}",
        f"    confirmed unavailable      {ie['unavailable']:>5}",
        f"    unclassified lead phrase   {unclassified_ie:>5}   (treated as unknown)",
        f"    no published Irish route   {no_route_count:>5}   (a kind of unknown, never unavailable)",
        "",
        f"  Missing price                 {payload['missingPriceCount']:>5}",
        f"  Missing Product URL           {payload['missingProductUrlCount']:>5}",
        "",
        "  Exclusions by reason",
    ] + [f"    {k}  {v:>5}" for k, v in sorted(blockers.items())] + [
        "", "  NOTHING WAS WRITTEN TO AIRTABLE. NOTHING PRODUCTION WAS TOUCHED.",
    ]
    report = "\n".join(lines) + "\n"
    (out / "garden-room-qualification-report.txt").write_text(report, encoding="utf-8")
    print(report)


if __name__ == "__main__":
    main()
