#!/usr/bin/env python3
"""VALIDATOR — Driveway Income evidence substrate. Schema plotnua.driveway.evidence.v1

   Reads driveway-evidence.json and refuses it if it says anything PlotNua has
   not earned the right to say.

   THE VALIDATOR IS NOT A SCHEMA CHECK. Structure is the cheap half. The
   expensive half is the set of propositions this journey is forbidden to
   carry, each of which was a real error someone made or nearly made:

     - the pre-2011 two-car limit (was live on the site until Gate 3D)
     - "never determined in Ireland" (a universal negative from a bounded search)
     - UNDETERMINED (an authority gap PlotNua has not established)
     - the EUR 5,000 self-assessment threshold (unverified, excluded from V1)
     - anecdotal earnings, marketplace prices, personalised value
     - demand or proximity scores, and any geospatial field at all
     - a universal duty to notify an insurer, or automatic voiding of cover

   EVERY CHECK FAILS CLEANLY. A check that raises instead of reporting is a
   defect in the validator, not a rejection of the manifest, and the harness
   scores it as such.

   Exit 0 = manifest is publishable. Exit 1 = it is not.
"""
import json
import pathlib
import re
import sys
from datetime import date, datetime

HERE = pathlib.Path(__file__).resolve().parents[2]
DEFAULT = HERE / "driveway-evidence.json"

SCHEMA = "plotnua.driveway.evidence.v1"
RESULTS = {"PERMISSION", "TAX", "INSURANCE", "THE_DRIVEWAY"}
EVIDENCE_TYPES = {"PUBLISHED_SOURCE", "ABSENCE_OF_RECORD", "JURISDICTION"}
MONEY_LEVELS = {"NONE", "SCHEME_THRESHOLD"}
STATUSES = {"CURRENT", "RECHECK_REQUIRED", "WITHHOLD", "SUPERSEDED",
            "NOT_YET_IN_FORCE"}
STALENESS_POLICIES = {"DOWNGRADE", "WITHHOLD", "SAFE_UNTIL_EXPIRY"}

REQUIRED = [
    "evidence_id", "result", "claim_key", "claim", "evidence_type",
    "jurisdiction", "authority", "source_type", "last_verified",
    "review_interval_months", "verification_method", "maturity",
    "verification_status", "homeowner_safe", "logic_safe", "staleness_policy",
    "conflicts_with", "supersedes", "superseded_by", "money_level",
    "prohibited_readings", "notes",
]

#  Claim keys the journey engine is entitled to bind to. A key outside this set
#  is an orphan; a key inside it that is missing is a hole the engine would hit
#  at runtime. Both are build failures.
SPEC_CLAIM_KEYS = {
    "planning_hardsurface_class_current",
    "planning_incidental_test_wording",
    "planning_no_exact_decision_located",
    "planning_related_decisions_exist",
    "planning_section5_route",
    "planning_england_guidance_not_applicable",
    "rent_a_room_scope_residential_rooms",
    "rent_a_room_limit_eur",
    "rent_a_room_exempt_from_prsi_usc",
    "driveway_income_is_taxable",
    "insurance_precontract_duty_scope",
    "insurance_misrepresentation_remedies_proportionate",
    "insurance_alteration_of_risk_limits",
    "insurance_no_irish_guidance_located",
}

#  Absence records must be re-searched more often than sources are re-read.
MAX_ABSENCE_REVIEW_MONTHS = 6

# ---------------------------------------------------------------------------
# PROHIBITED PROPOSITIONS. Matched against every string the manifest carries.
# ---------------------------------------------------------------------------
BANNED_TEXT = [
    # -- the repealed planning rule ------------------------------------------
    (r"not more than (?:2|two) (?:motor vehicles|cars)",
     "the pre-2011 two-car limit; repealed by S.I. 454/2011"),
    (r"(?:limit(?:ed)? (?:of|to) )?(?:2|two) cars? (?:only|maximum|max)",
     "the pre-2011 two-car limit"),
    # -- the universal negative ----------------------------------------------
    (r"never been (?:publicly )?determined",
     "universal negative: a bounded search cannot establish it"),
    (r"never determined in ireland", "universal negative"),
    (r"no irish decision exists", "universal negative"),
    (r"has not been determined(?! in the records)", "universal negative"),
    (r"no (?:published )?determination exists", "universal negative"),
    # -- money PlotNua will not carry ----------------------------------------
    (r"(?:eur\s*|€)\s*5[,.]?000", "the EUR 5,000 self-assessment threshold; "
                                  "excluded from V1"),
    (r"form 11\b", "self-assessment filing route; excluded from V1"),
    (r"form 12\b", "self-assessment filing route; excluded from V1"),
    (r"(?:eur\s*|€)\s*\d+\s*(?:a|per)\s*(?:week|day|month|night|year)",
     "anecdotal earnings"),
    (r"\b(?:yourparkingspace|justpark|parkpnp|daft\.ie|rent\.ie)\b",
     "marketplace price or listing source"),
    (r"\bper (?:day|week|night) rate\b", "marketplace price"),
    (r"\byou could (?:earn|make)\b", "personalised value"),
    (r"\byour driveway is worth\b", "personalised value"),
    (r"\b(?:estimated|projected|potential) (?:income|earnings|revenue|yield)\b",
     "earnings estimate"),
    # -- inference PlotNua does not do ---------------------------------------
    (r"\bdemand (?:score|rating|index)\b", "demand score"),
    (r"\bproximity (?:score|rating|index)\b", "proximity score"),
    (r"\bfootfall\b", "demand inference"),
    (r"\bnearby (?:poi|points of interest)\b", "POI inference"),
    # -- the state that is not available ------------------------------------
    (r"\bundetermined\b", "UNDETERMINED is not available in V1"),
    # -- insurance overreach --------------------------------------------------
    (r"must (?:notify|tell|inform) (?:your |their |the )?insurer",
     "universal duty to notify; contradicts CICA 2019 s.8"),
    (r"(?:duty|obligation) to (?:notify|disclose to|inform) (?:your |their |the )?insurer",
     "universal duty to notify"),
    (r"(?:will|can|may) (?:automatically )?(?:void|invalidate) (?:your |their |the )?(?:policy|cover)",
     "automatic policy avoidance"),
    (r"(?:policy|cover) (?:is|will be) (?:automatically )?void",
     "automatic policy avoidance"),
    (r"\b(?:is|are) (?:definitely |certainly )?(?:covered|excluded)\b",
     "guaranteed cover or exclusion"),
]

#  Field names that must not exist anywhere in the manifest, at any depth.
BANNED_FIELDS = {
    "lat", "lng", "lon", "latitude", "longitude", "coordinates", "coords",
    "eircode", "easting", "northing", "itm_x", "itm_y", "geometry", "geojson",
    "bbox", "radius_m", "distance_m", "nearest", "poi", "pois",
    "demand_score", "proximity_score", "earnings", "estimated_income",
    "price_per_day", "price_per_week", "market_rate",
}

#  A record must be able to NAME the proposition it forbids. Two fields exist
#  for exactly that, and only those two are exempt from the text scan:
#
#      record.prohibited_readings[]         — "this record must not be read as X"
#      record.search_scope.conclusion_prohibited
#
#  Nothing else is exempt. In particular `notes` is fully scanned, because notes
#  are prose and prose drifts into assertion. If a governance point cannot be
#  made without stating a banned proposition, it belongs in prohibited_readings,
#  which is structured, declared, and never rendered to a homeowner.
PROHIBITION_FIELDS = ("prohibited_readings", "conclusion_prohibited")


def is_prohibition_field(path):
    return any(f".{f}" in path for f in PROHIBITION_FIELDS)


ERRORS = []


def fail(where, msg):
    ERRORS.append(f"{where}: {msg}")


def walk_strings(node, path="$"):
    """Yield (path, string) for every string anywhere in the document."""
    if isinstance(node, str):
        yield path, node
    elif isinstance(node, dict):
        for k, v in node.items():
            yield from walk_strings(v, f"{path}.{k}")
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from walk_strings(v, f"{path}[{i}]")


def walk_keys(node, path="$"):
    if isinstance(node, dict):
        for k, v in node.items():
            yield path, k
            yield from walk_keys(v, f"{path}.{k}")
    elif isinstance(node, list):
        for i, v in enumerate(node):
            yield from walk_keys(v, f"{path}[{i}]")


def parse_date(s):
    try:
        return datetime.strptime(s, "%Y-%m-%d").date()
    except Exception:
        return None


def main():
    path = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT
    if not path.exists():
        print(f"FAIL: {path} does not exist")
        return 1
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        print(f"FAIL: {path} is not valid JSON: {e}")
        return 1

    # ---------------------------------------------------------------- envelope
    if doc.get("schema") != SCHEMA:
        fail("$.schema", f"expected {SCHEMA}, got {doc.get('schema')!r}")
    if doc.get("jurisdiction") != "IE-ROI":
        fail("$.jurisdiction", "must be IE-ROI")
    gen = parse_date(doc.get("generated", ""))
    if gen is None:
        fail("$.generated", "missing or not YYYY-MM-DD")
    records = doc.get("records")
    if not isinstance(records, list):
        print("FAIL: $.records is missing or not a list")
        return 1
    if doc.get("recordCount") != len(records):
        fail("$.recordCount", f"says {doc.get('recordCount')}, "
                             f"found {len(records)}")

    # ------------------------------------------------------- banned field names
    for where, key in walk_keys(doc):
        if key.lower() in BANNED_FIELDS:
            fail(where, f"prohibited field name {key!r} (geospatial, demand or "
                        f"value inference has no place in this journey)")

    # ------------------------------------------------------------ banned text
    for where, text in walk_strings(doc):
        if is_prohibition_field(where):
            continue          # this field exists to name prohibitions
        haystack = text.lower()
        for pattern, why in BANNED_TEXT:
            if re.search(pattern, haystack):
                fail(where, f"prohibited proposition ({why}): "
                            f"matched /{pattern}/")

    # --------------------------------------------------------------- records
    seen_ids, seen_keys = set(), {}
    by_result = {}
    for i, rec in enumerate(records):
        #  Type-guard FIRST. Everything below assumes a mapping, and a validator
        #  that raises on malformed input has not rejected it — it has merely
        #  stopped, with an exit code nobody should trust.
        if not isinstance(rec, dict):
            fail(f"$.records[{i}]", f"record is {type(rec).__name__}, not an "
                                    f"object")
            continue
        rid = rec.get("evidence_id", f"<record {i}>")
        w = f"$.records[{i}] ({rid})"

        missing = [f for f in REQUIRED if f not in rec]
        if missing:
            fail(w, f"missing required field(s): {', '.join(missing)}")
            continue

        if rec["evidence_id"] in seen_ids:
            fail(w, f"duplicate evidence_id {rec['evidence_id']!r}")
        seen_ids.add(rec["evidence_id"])

        #  One record per claim_key. Two records answering to the same key means
        #  the engine's answer depends on iteration order.
        if rec["claim_key"] in seen_keys:
            fail(w, f"duplicate claim_key {rec['claim_key']!r} "
                    f"(already used by {seen_keys[rec['claim_key']]})")
        seen_keys[rec["claim_key"]] = rec["evidence_id"]

        if rec["result"] not in RESULTS:
            fail(w, f"invalid result {rec['result']!r}")
        by_result[rec["result"]] = by_result.get(rec["result"], 0) + 1

        if rec["evidence_type"] not in EVIDENCE_TYPES:
            fail(w, f"invalid evidence_type {rec['evidence_type']!r}")
        if rec["money_level"] not in MONEY_LEVELS:
            fail(w, f"invalid money_level {rec['money_level']!r} "
                    f"(permitted: {sorted(MONEY_LEVELS)})")
        if rec["verification_status"] not in STATUSES:
            fail(w, f"invalid verification_status {rec['verification_status']!r}")
        if rec["staleness_policy"] not in STALENESS_POLICIES:
            fail(w, f"invalid staleness_policy {rec['staleness_policy']!r}")

        lv = parse_date(rec.get("last_verified") or "")
        if lv is None:
            fail(w, "last_verified missing or not YYYY-MM-DD")

        if not isinstance(rec.get("review_interval_months"), int) or \
                rec["review_interval_months"] <= 0:
            fail(w, "review_interval_months must be a positive integer")

        # ------------------------------------------- ABSENCE_OF_RECORD rules
        if rec["evidence_type"] == "ABSENCE_OF_RECORD":
            scope = rec.get("search_scope")
            if not isinstance(scope, dict) or not scope:
                fail(w, "ABSENCE_OF_RECORD without a search_scope. An absence "
                        "that does not state what was searched is a universal "
                        "negative wearing a badge.")
            else:
                for f in ("searched_on", "registers_searched", "terms",
                          "limitations"):
                    if not scope.get(f):
                        fail(w, f"search_scope.{f} is missing or empty")
                if scope.get("searched_on") and parse_date(scope["searched_on"]) is None:
                    fail(w, "search_scope.searched_on is not YYYY-MM-DD")
                regs = scope.get("registers_searched")
                if isinstance(regs, list):
                    for j, reg in enumerate(regs):
                        if not isinstance(reg, dict) or not reg.get("register") \
                                or not reg.get("coverage"):
                            fail(w, f"search_scope.registers_searched[{j}] must "
                                    f"name a register and its coverage")
            if not rec.get("prohibited_readings"):
                fail(w, "ABSENCE_OF_RECORD without prohibited_readings. An "
                        "absence record must state, in a machine-readable "
                        "field, what it may not be read as.")
            if lv is None:
                fail(w, "ABSENCE_OF_RECORD without last_verified")
            ri = rec.get("review_interval_months")
            if isinstance(ri, int) and ri > MAX_ABSENCE_REVIEW_MONTHS:
                fail(w, f"ABSENCE_OF_RECORD review_interval_months is {ri}; "
                        f"maximum is {MAX_ABSENCE_REVIEW_MONTHS}. An absence "
                        f"can be filled without any document changing.")
            if rec["staleness_policy"] != "WITHHOLD":
                fail(w, "ABSENCE_OF_RECORD must carry staleness_policy "
                        "WITHHOLD so a stale absence is never served as current")
            #  Recompute staleness independently of the generator.
            if lv and gen:
                elapsed = (gen.year - lv.year) * 12 + (gen.month - lv.month) \
                          - (1 if gen.day < lv.day else 0)
                if elapsed >= rec["review_interval_months"] and \
                        rec["verification_status"] == "CURRENT":
                    fail(w, f"stale absence ({elapsed} months since "
                            f"last_verified) is still marked CURRENT")

        # --------------------------------------------- logic_safe requires proof
        if rec.get("logic_safe") and rec["verification_method"] in (None, "",
                                                                    "ASSERTED"):
            fail(w, "logic_safe record without a real verification_method")
        if rec.get("logic_safe") and rec["evidence_type"] == "PUBLISHED_SOURCE" \
                and not rec.get("source_url"):
            fail(w, "logic_safe PUBLISHED_SOURCE without a source_url")

        # ------------------------------------- resolved flags must be coherent
        if rec["verification_status"] != "CURRENT":
            if rec.get("homeowner_safe_resolved") or rec.get("logic_safe_resolved"):
                fail(w, f"status is {rec['verification_status']} but a resolved "
                        f"safety flag is still true")

        # --------------------- SCHEME_THRESHOLD must actually carry a threshold
        if rec["money_level"] == "SCHEME_THRESHOLD":
            v = rec.get("value") or {}
            if not isinstance(v, dict) or "amount" not in v or "currency" not in v:
                fail(w, "money_level SCHEME_THRESHOLD without value.amount and "
                        "value.currency")
        if rec["money_level"] == "NONE":
            v = rec.get("value")
            if isinstance(v, dict) and any(
                    k in v for k in ("amount", "price", "rate", "income")):
                fail(w, "money_level NONE but value carries a monetary field")

    # ------------------------------------------------------- claim-key coverage
    present = set(seen_keys)
    missing = sorted(SPEC_CLAIM_KEYS - present)
    if missing:
        fail("$.records", f"claim_key(s) the engine expects are absent: "
                          f"{', '.join(missing)}")
    orphans = sorted(present - SPEC_CLAIM_KEYS)
    if orphans:
        fail("$.records", f"claim_key(s) not in the engine spec: "
                          f"{', '.join(orphans)}")

    # -------------------------------------------- THE DRIVEWAY carries no evidence
    if by_result.get("THE_DRIVEWAY"):
        fail("$.records", "THE_DRIVEWAY must carry no evidence records. It is "
                          "answered from the homeowner's own answers, never "
                          "from a source or an inference.")

    # ------------------------------------- the absence must never stand alone
    if "planning_no_exact_decision_located" in present and \
            "planning_related_decisions_exist" not in present:
        fail("$.records", "the planning absence record is present without "
                          "planning_related_decisions_exist. Presenting the "
                          "absence alone implies a silence that the search did "
                          "not find.")

    # ------------------------------------------------------------------ report
    if ERRORS:
        print(f"FAIL: {len(ERRORS)} problem(s) in {path.name}\n")
        for e in ERRORS:
            print(f"  - {e}")
        return 1

    print(f"OK: {path.name}")
    print(f"  schema          : {doc['schema']}")
    print(f"  generated       : {doc['generated']}")
    print(f"  records         : {len(records)}")
    print(f"  by result       : {by_result}")
    print(f"  absence records : "
          f"{sum(1 for r in records if r['evidence_type'] == 'ABSENCE_OF_RECORD')}"
          f" (all scoped, all WITHHOLD-on-stale)")
    print(f"  claim keys      : {len(present)}/{len(SPEC_CLAIM_KEYS)} covered, "
          f"0 orphans")
    return 0


if __name__ == "__main__":
    sys.exit(main())
