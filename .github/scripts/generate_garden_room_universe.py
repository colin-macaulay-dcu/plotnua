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

    So this script reads Confirmation State FIRST where it exists, and falls
    back to a strict prefix match on Value Text. Any lead phrase not in the
    vocabulary below resolves to UNKNOWN — never to unavailable — and is
    counted in unclassifiedIrishAvailabilityCount so the blind spot is visible
    rather than silent. Fixing the underlying field is Atlas work, not
    qualification work, and is reported rather than papered over.

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
}

# ── Irish availability vocabulary ────────────────────────────────────────────
# Deterministic, ordered, and deliberately asymmetric: the "unavailable"
# vocabulary must be an explicit statement that the product cannot be had in
# the Republic. Everything unrecognised is UNKNOWN.
IE_CONFIRMED = (
    "AVAILABLE ACROSS IRELAND",
    "AVAILABLE IN IRELAND",
    "AVAILABLE IN THE REPUBLIC OF IRELAND",
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

# A contradiction is only a hard blocker when Atlas has RECORDED one. These are
# the recorded markers; nothing is inferred from ordinary prose.
CONTRADICTION_MARKERS = (
    "UNRESOLVED CONTRADICTION",
    "CONTRADICTION UNRESOLVED",
    "DATA CONFLICT",
    "CONFLICTING EVIDENCE",
)
CONTRADICTION_STATUSES = ("Contradicted", "Conflict", "Disputed")

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


# ── qualification ────────────────────────────────────────────────────────────
def classify_irish_availability(feat_rows: list) -> tuple:
    """(state, basis, scope, classified) — state is confirmed|unknown|unavailable.

    Confirmation State wins when populated: it is the field the schema intends,
    and its own description forbids treating Unknown as No. Value Text is the
    documented fallback. `classified` is False when a lead phrase was present
    but matched no vocabulary — that product still resolves to UNKNOWN, and the
    caller counts it so the parser's blind spots are visible rather than
    silently becoming verdicts."""
    best = ("unknown", "no irish-availability evidence recorded", None)
    classified = True
    for row in feat_rows:
        scope = cell(row, "Evidence Scope")
        conf = txt(cell(row, "Confirmation State"))
        if conf:
            c = conf.lower()
            if c.startswith("yes"):
                return ("confirmed", f"Confirmation State: {conf}", scope, True)
            if c == "no":
                return ("unavailable", f"Confirmation State: {conf}", scope, True)
            if c == "unknown":
                best = ("unknown", f"Confirmation State: {conf}", scope)
                continue
        body = txt(cell(row, "Value Text"))
        if not body:
            continue
        head = body.upper()
        if any(head.startswith(p) for p in IE_UNAVAILABLE):
            return ("unavailable", body[:200], scope, True)
        if any(head.startswith(p) for p in IE_CONFIRMED):
            return ("confirmed", body[:200], scope, True)
        if any(head.startswith(p) for p in IE_UNKNOWN):
            best = ("unknown", body[:200], scope)
            continue
        classified = False
        best = ("unknown", body[:200], scope)
    return best + (classified,)


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


def qualify(product, orgs, price_rows, avail_rows, feat_rows) -> dict:
    """Deterministic. Same inputs, same output, every run."""
    name = txt(cell(product, "Product Name"))
    org_ids = links(product, "Organisation")
    org_names = [orgs.get(i, {}).get("name", "") for i in org_ids]
    url = txt(cell(product, "Product URL"))
    sources_text = txt(cell(product, "    Sources"))
    ie_state, ie_basis, ie_scope, ie_classified = classify_irish_availability(feat_rows)
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
    if ie_state == "unknown":
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
    elif price_state == "missing" and source_level in ("range-level", "missing"):
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
                "organisations": fetch_all(token, T_ORGS, ["Organisation Name", "Organisation Type", "Website"]),
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
    unclassified_ie = 0
    for p in sorted(garden, key=lambda r: (txt(cell(r, "Product Name")), r["id"])):
        pid = p["id"]
        fv = by_product["featureValues"].get(pid, [])
        ie_rows = [r for r in fv if set(links(r, "Feature")) & ie_feature_ids] or [
            r for r in fv if "irish availability" in txt(cell(r, "Product Feature Value Name")).lower()]
        q = qualify(p, orgs, by_product["pricing"].get(pid, []),
                    by_product["availability"].get(pid, []), ie_rows)
        if not q["evidenceSignals"]["irishAvailabilityClassified"]:
            unclassified_ie += 1

        rec = {
            "productId": pid,
            "productCode": txt(cell(p, "Product Code")),
            "productName": txt(cell(p, "Product Name")),
            "productType": txt(cell(p, "Product Type")),
            "productCategory": txt(cell(p, "Product Category")),
            "organisation": [{"id": i, "name": orgs.get(i, {}).get("name", "")}
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
            rec["price"] = None if not pick else {
                "base": cell(pick, "Base Price"), "from": cell(pick, "Price From"),
                "to": cell(pick, "Price To"), "currency": cell(pick, "Currency"),
                "priceType": cell(pick, "Price Type"), "status": cell(pick, "Status"),
                "includesVat": cell(pick, "Price Includes VAT"),
                "evidenceScope": cell(pick, "Evidence Scope"),
            }
            carried = {}
            for r in by_product["featureValues"].get(pid, []):
                fname = next((features.get(i, "") for i in links(r, "Feature")), "")
                key = FEATURES_WANTED.get(fname.lower())
                if key and key not in carried:
                    carried[key] = {"text": txt(cell(r, "Value Text")) or None,
                                    "number": cell(r, "Value Number"),
                                    "unit": cell(r, "Unit"),
                                    "evidenceScope": cell(r, "Evidence Scope")}
            rec["features"] = carried
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
