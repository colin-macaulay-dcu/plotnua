#!/usr/bin/env python3
"""
PlotNua — DISC-026 evidence manifest: PRODUCTION VALIDATION GATE.

    validate_disc026_evidence.py --candidate CAND [--production PROD]
                                 [--summary-out FILE] [--github-output]

    exit 0  candidate is valid          exit 1  candidate is REJECTED

Stands between a freshly generated manifest and the file the homeowner's browser
loads. Nothing reaches production without passing here.

WHAT IT CHECKS, AND WHY EACH ONE EXISTS.

  Structure, so the runtime can read it. Vocabulary, so an unknown never arrives
  as a fact. Temporal sanity, so an expired rule cannot pose as current. And a
  small set of TRUTHFULNESS bans that exist because this journey's whole claim is
  that it does not make up numbers: no supplier tariff rate, no savings or
  earnings estimate, no invented 2027 grant amount, no post-2028 tax exemption
  presented as current.

  It also enforces the CONTRACT with the frozen Gate 5 interaction specification:
  every claim_key the journey binds to must exist, and no record may claim to be
  engine-facing while being unreachable by any of them.

LAST-KNOWN-GOOD PROTECTION.

  --production is optional but, when given, enables the one relative guard: a
  candidate holding fewer than half the production records is refused. It is
  proportional, so it never blocks growth — only a collapse. A partial or empty
  generation is exactly what that catches, and a human should look at it.
"""
import argparse
import json
import os
import re
import sys
from datetime import date, datetime
from pathlib import Path

SCHEMA = "plotnua.disc026.evidence.v1"

OPPORTUNITIES = {"MAKE", "TIME", "STORE", "SELL", "CROSS"}
JURISDICTIONS = {"IE", "IE-ROI", "EU", "NON-IE"}
AUTHORITIES = {"SEAI", "CRU", "ESB_NETWORKS", "REVENUE", "GOV_IE", "OIREACHTAS",
               "CITIZENS_INFO", "SUPPLIER", "NSAI"}
SOURCE_TYPES = {"STATUTE_SI", "REGULATOR_DECISION", "SCHEME_PAGE",
                "OPERATOR_STANDARD", "TAX_RULE", "PRESS_RELEASE", "SECONDARY"}
MATURITY = {"CURRENT_RULE", "CURRENT_SCHEME", "CURRENT_REGULATORY_REQUIREMENT",
            "TIME_LIMITED", "ANNOUNCED_FUTURE_CHANGE", "PILOT", "SUPERSEDED"}
RESOLVED = {"CURRENT", "RECHECK_REQUIRED", "WITHHOLD", "SUPERSEDED",
            "NOT_YET_IN_FORCE"}
STALENESS = {"WITHHOLD", "DOWNGRADE", "SAFE_UNTIL_EXPIRY"}
METHODS = {"PRIMARY_FETCH", "PDF_READ", "REMOTE_QUERY", "MANUAL_CONFIRMATION"}

REQUIRED = ["evidence_id", "opportunity", "claim_key", "claim", "jurisdiction",
            "authority", "source_title", "source_url", "source_type",
            "last_verified", "review_interval_months", "verification_method",
            "maturity", "homeowner_safe", "logic_safe", "staleness_policy",
            "resolved_status"]

# The contract with DISC-026-V1-INTERACTION-SPEC.md. Every claim_key the frozen
# V1 journey binds to. A manifest missing any of these cannot drive the journey.
SPEC_REQUIRED_CLAIM_KEYS = {
    # MAKE
    "grant_structure", "grant_max_eur", "grant_requires_pre_2021",
    "grant_once_per_mprn", "grant_requires_mprn", "grant_eligible_applicants",
    "planning_exempt_houses", "planning_no_area_limit_houses",
    "planning_protected_structure_aca", "seai_does_not_warranty_contractor",
    # TIME
    "meter_enables_time_of_use", "meter_is_not_tariff",
    # STORE
    "battery_grant_exists", "ac_battery_treated_as_microgeneration",
    "battery_requires_esbn_notification", "battery_requires_safe_electric_rec",
    "battery_route_by_capacity",
    # SELL
    "supplier_must_pay_for_export", "export_state_metered",
    "export_state_waiting", "export_state_calculated", "export_state_declined",
    "export_requires_registration", "export_rates_unregulated",
    "microgen_income_tax_exemption", "mss_eligibility",
}

ISO = re.compile(r"^\d{4}-\d{2}-\d{2}$")

# Truthfulness bans. A ban token must be a string that cannot occur innocently
# in this manifest's own vocabulary.
RATE_PATTERNS = [
    re.compile(r"\d+\s*(?:c|cent|cents)\s*/\s*kWh", re.I),
    re.compile(r"\bper\s+kWh\b", re.I),
    re.compile(r"\bexport\s+rate\s+of\b", re.I),
    re.compile(r"€\s*\d+(?:\.\d+)?\s*/\s*kWh"),
]
EARNINGS_PATTERNS = [
    re.compile(r"\byou (?:could|would|can) (?:earn|save)\b", re.I),
    re.compile(r"\b(?:annual|yearly) (?:savings|earnings|income) of\b", re.I),
    re.compile(r"\bpayback (?:period )?of\b", re.I),
    re.compile(r"\bestimated (?:savings|earnings|generation)\b", re.I),
]


def d(s):
    return datetime.strptime(s, "%Y-%m-%d").date()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--candidate", required=True)
    ap.add_argument("--production", default=None)
    ap.add_argument("--summary-out", default=None)
    ap.add_argument("--github-output", action="store_true")
    ap.add_argument("--min-retained-fraction", type=float, default=0.5)
    a = ap.parse_args()

    errors, warnings, stats = [], [], {}

    # 1 · valid JSON -------------------------------------------------------
    raw = Path(a.candidate).read_text(encoding="utf-8")
    try:
        doc = json.loads(raw)
    except Exception as e:                                       # noqa: BLE001
        print(f"  REJECTED — candidate is not valid JSON: {e}")
        return 1

    # 2 · schema / version -------------------------------------------------
    if doc.get("schema") != SCHEMA:
        errors.append(f"schema is {doc.get('schema')!r}, expected {SCHEMA!r}")
    if not ISO.match(str(doc.get("generated", ""))):
        errors.append("generated is not an ISO date")
    records = doc.get("records")
    if not isinstance(records, list) or not records:
        print("  REJECTED — no records array. Production is NOT replaced.")
        return 1
    stats["records"] = len(records)
    if doc.get("recordCount") != len(records):
        errors.append(f"recordCount {doc.get('recordCount')} != {len(records)}")

    as_of = d(doc["generated"]) if ISO.match(str(doc.get("generated", ""))) else date.today()

    ids, keys = set(), {}
    serveable_keys = set()

    for i, rec in enumerate(records):
        tag = rec.get("evidence_id") or f"record[{i}]"

        # 5 · required fields ---------------------------------------------
        for f in REQUIRED:
            if f not in rec or rec[f] is None or rec[f] == "":
                errors.append(f"{tag}: missing required field {f!r}")
        if any(f not in rec for f in REQUIRED):
            continue

        # 3 · unique evidence_id ------------------------------------------
        if rec["evidence_id"] in ids:
            errors.append(f"{tag}: duplicate evidence_id")
        ids.add(rec["evidence_id"])

        # 4 · claim_key uniqueness among servable records ------------------
        keys.setdefault(rec["claim_key"], []).append(rec["evidence_id"])

        # 6 · enums --------------------------------------------------------
        for field, allowed in (("opportunity", OPPORTUNITIES),
                               ("jurisdiction", JURISDICTIONS),
                               ("authority", AUTHORITIES),
                               ("source_type", SOURCE_TYPES),
                               ("maturity", MATURITY),
                               ("resolved_status", RESOLVED),
                               ("staleness_policy", STALENESS),
                               ("verification_method", METHODS)):
            if rec[field] not in allowed:
                errors.append(f"{tag}: {field}={rec[field]!r} not in vocabulary")
        for b in ("homeowner_safe", "logic_safe"):
            if not isinstance(rec[b], bool):
                errors.append(f"{tag}: {b} must be boolean")
        if not isinstance(rec["review_interval_months"], int) or \
                not 1 <= rec["review_interval_months"] <= 60:
            errors.append(f"{tag}: review_interval_months out of range")
        if not str(rec["source_url"]).startswith("https://"):
            errors.append(f"{tag}: source_url is not https")

        # 7 · date formats -------------------------------------------------
        for f in ("valid_from", "valid_until", "last_verified",
                  "source_published_date"):
            if rec.get(f) is not None and not ISO.match(str(rec[f])):
                errors.append(f"{tag}: {f} is not an ISO date")

        # 8 · temporal ordering --------------------------------------------
        try:
            vf = d(rec["valid_from"]) if rec.get("valid_from") else None
            vu = d(rec["valid_until"]) if rec.get("valid_until") else None
            lv = d(rec["last_verified"])
            if vf and vu and vu < vf:
                errors.append(f"{tag}: valid_until precedes valid_from")
            if lv > as_of:
                errors.append(f"{tag}: last_verified is in the future")
            sp = d(rec["source_published_date"]) if rec.get("source_published_date") else None
            if sp and sp > as_of:
                errors.append(f"{tag}: source_published_date is in the future")

            # 9 · no CURRENT record past valid_until -----------------------
            if vu and vu < as_of and rec["resolved_status"] == "CURRENT":
                errors.append(f"{tag}: CURRENT but valid_until {rec['valid_until']} "
                              f"has passed — expired evidence must not stay TRUE")
        except Exception as e:                                   # noqa: BLE001
            errors.append(f"{tag}: date parse failure: {e}")

        # ANNOUNCED_FUTURE_CHANGE must never be engine-facing ---------------
        if rec["maturity"] == "ANNOUNCED_FUTURE_CHANGE":
            if rec["logic_safe"]:
                errors.append(f"{tag}: ANNOUNCED_FUTURE_CHANGE must not be logic_safe")
            if rec["resolved_status"] == "CURRENT":
                errors.append(f"{tag}: ANNOUNCED_FUTURE_CHANGE resolved CURRENT")

        # 10 · logic_safe records need a usable resolved status --------------
        rs = rec["resolved_status"]
        if rec.get("logic_safe_resolved") and rs != "CURRENT":
            errors.append(f"{tag}: logic_safe_resolved true with status {rs}")

        # 11 · WITHHOLD cannot be served as homeowner-safe current ----------
        if rs in ("WITHHOLD", "SUPERSEDED", "RECHECK_REQUIRED", "NOT_YET_IN_FORCE"):
            if rec.get("homeowner_safe_resolved"):
                errors.append(f"{tag}: {rs} but homeowner_safe_resolved is true")
        if rs == "CURRENT":
            serveable_keys.add(rec["claim_key"])

        # 12/13 · supersession and conflict references resolve --------------
        for f in ("supersedes", "superseded_by"):
            v = rec.get(f)
            if v and v not in {r_.get("evidence_id") for r_ in records}:
                errors.append(f"{tag}: {f} -> {v!r} does not resolve")
        for c in rec.get("conflicts_with") or []:
            if c not in {r_.get("evidence_id") for r_ in records}:
                errors.append(f"{tag}: conflicts_with -> {c!r} does not resolve")
            if rs != "WITHHOLD":
                errors.append(f"{tag}: has a conflict but is not WITHHOLD")

        # 14/15 · truthfulness bans ----------------------------------------
        blob = json.dumps(rec, ensure_ascii=False)
        for p in RATE_PATTERNS:
            if p.search(blob):
                errors.append(f"{tag}: contains what looks like a supplier "
                              f"tariff rate ({p.pattern})")
        for p in EARNINGS_PATTERNS:
            if p.search(blob):
                errors.append(f"{tag}: contains a savings or earnings estimate "
                              f"({p.pattern})")
        if rec["authority"] == "SUPPLIER" and rec.get("homeowner_safe"):
            warnings.append(f"{tag}: supplier-sourced and homeowner_safe — check")

    # 4 · claim_key uniqueness among CURRENT records ------------------------
    for k, owners in keys.items():
        current_owners = [o for o in owners
                          if next(r_ for r_ in records if r_.get("evidence_id") == o)
                          .get("resolved_status") == "CURRENT"]
        if len(current_owners) > 1:
            errors.append(f"claim_key {k!r} is CURRENT on more than one record: "
                          f"{current_owners}")

    # 16 · no invented 2027+ grant amount -----------------------------------
    for rec in records:
        if rec.get("claim_key") == "grant_max_eur":
            v = (rec.get("value") or {}).get("year")
            if isinstance(v, int) and v > 2026 and rec.get("last_verified", "") <= "2026-12-31":
                errors.append(f"{rec['evidence_id']}: a post-2026 grant maximum "
                              f"appears without later verification — never invent one")

    # 17 · no post-2028 tax exemption presented as current -------------------
    for rec in records:
        if rec.get("claim_key") == "microgen_income_tax_exemption":
            vu = rec.get("valid_until")
            if vu and d(vu) < as_of and rec.get("resolved_status") == "CURRENT":
                errors.append(f"{rec['evidence_id']}: expired tax exemption "
                              f"presented as CURRENT")
            if vu and d(vu) > date(2028, 12, 31):
                errors.append(f"{rec['evidence_id']}: tax exemption extended "
                              f"beyond 2028 without verification")

    # 18 · every claim_key the frozen spec needs exists ----------------------
    present = set(keys)
    missing = sorted(SPEC_REQUIRED_CLAIM_KEYS - present)
    for m in missing:
        errors.append(f"claim_key {m!r} is required by the frozen V1 "
                      f"interaction spec but is absent")

    # 19 · no orphan engine-facing claim_keys --------------------------------
    engine_keys = {r_["claim_key"] for r_ in records
                   if r_.get("logic_safe") and r_.get("claim_key")}
    orphans = sorted(engine_keys - SPEC_REQUIRED_CLAIM_KEYS)
    for o in orphans:
        warnings.append(f"claim_key {o!r} is logic_safe but the frozen spec "
                        f"does not bind to it — dead engine surface")

    # 20 · last-known-good protection ----------------------------------------
    changed = True
    if a.production and Path(a.production).exists():
        prod_raw = Path(a.production).read_text(encoding="utf-8")
        changed = prod_raw != raw
        try:
            prod = json.loads(prod_raw)
            pn = len(prod.get("records", []))
            if pn and len(records) < pn * a.min_retained_fraction:
                errors.append(f"candidate retains {len(records)} of {pn} production "
                              f"records — below {a.min_retained_fraction:.0%}. "
                              f"Refusing: this looks like a partial generation.")
        except Exception:                                        # noqa: BLE001
            warnings.append("production manifest is unreadable — treated as absent")

    by_opp, by_status = {}, {}
    for rec in records:
        by_opp[rec.get("opportunity")] = by_opp.get(rec.get("opportunity"), 0) + 1
        by_status[rec.get("resolved_status")] = by_status.get(rec.get("resolved_status"), 0) + 1
    stats.update({f"opp_{k}": v for k, v in by_opp.items()})
    stats.update({f"status_{k}": v for k, v in by_status.items()})
    stats["serveable_claim_keys"] = len(serveable_keys)

    lines = ["", "DISC-026 EVIDENCE MANIFEST — VALIDATION", ""]
    lines.append(f"  candidate       : {a.candidate}")
    lines.append(f"  generated as-of : {doc.get('generated')}")
    lines.append(f"  records         : {len(records)}  {by_opp}")
    lines.append(f"  resolved        : {by_status}")
    lines.append(f"  CURRENT keys    : {len(serveable_keys)}")
    if warnings:
        lines.append("")
        for w in warnings[:15]:
            lines.append(f"  warning  - {w}")
    lines.append("")
    if errors:
        lines.append(f"  REJECTED — {len(errors)} problem(s). Production is NOT replaced.")
        for e in errors[:25]:
            lines.append(f"    - {e}")
        if len(errors) > 25:
            lines.append(f"    …and {len(errors) - 25} more")
    else:
        lines.append("  VALID — candidate is safe to publish.")

    report = "\n".join(lines)
    print(report)
    if a.summary_out:
        Path(a.summary_out).write_text(report + "\n", encoding="utf-8")
    if a.github_output and os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as fh:
            fh.write(f"changed={'true' if (changed and not errors) else 'false'}\n")
            fh.write(f"valid={'true' if not errors else 'false'}\n")
            for k, v in stats.items():
                fh.write(f"{k}={v}\n")

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
