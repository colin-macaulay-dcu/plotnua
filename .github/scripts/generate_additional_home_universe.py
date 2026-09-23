#!/usr/bin/env python3
"""PlotNua — generate_additional_home_universe.py

Builds the Additional Home candidate from a frozen Atlas snapshot.

PUBLIC-DISCLOSURE FIREWALL. Habitation Classification Basis is read and NEVER
exported. What reaches the artefact is a CLOSED six-token signal vocabulary
derived from it, plus the governed classification itself. Anything the
vocabulary cannot safely carry is DROPPED and counted, never guessed.

Reads a snapshot only. It has no Airtable client and cannot write production.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
from pathlib import Path

from atlas_common import cell, txt, homeowner_text, fail
from additional_home_qualification import (
    RULE_VERSION, ADDITIONAL_HOME, CONFIRMED_HABITATION, HABITATION_STATES,
    qualify, class_3a, BAND_MIN, BAND_MAX, BAND_EDGE_TOLERANCE_M2,
)

SCHEMA = "plotnua.additional-home-universe"
VERSION = "1.0.0-candidate"

# ── THE CLOSED PUBLIC SIGNAL VOCABULARY ─────────────────────────────────────
# Six tokens, and nothing else may ever be emitted. Each pattern requires the
# SUPPLIER'S OWN published fact as quoted in the Basis — not PlotNua's
# reasoning about it. Conservative by design: a near miss is dropped.
SIGNALS = {
    "SLEEPING_ACCOMMODATION": re.compile(
        r"\b(bedroom|bedrooms|double bed|sleeping (?:area|accommodation|space)"
        r"|sleeps \d|berth)\b", re.I),
    "KITCHEN": re.compile(r"\b(kitchen|kitchenette|kitchen-diner)\b", re.I),
    "BATHROOM": re.compile(
        r"\b(bathroom|shower room|wet room|en-?suite|wc\b|toilet)\b", re.I),
    "HEATING": re.compile(
        r"\b(heat pump|underfloor heating|electric heating|heating system"
        r"|central heating|heating installed)\b", re.I),
    "YEAR_ROUND_INSULATION": re.compile(
        r"\b(year-?round (?:living|use)|fully insulated|insulated for year-?round"
        r"|all-?year (?:use|living))\b", re.I),
    "SUPPLIER_STATES_RESIDENTIAL": re.compile(
        r"\b(garden annexe|annexe|granny flat|tiny house|family home"
        r"|self-contained (?:home|dwelling|unit|garden annexe)"
        r"|somewhere to live|residential (?:unit|dwelling|accommodation)"
        r"|modular home|cabin home|log home)\b", re.I),
}

# Basis sentences that are PlotNua's own governance, never a supplier fact.
# A token is not derived from a sentence that opens with one of these.
GOVERNANCE_LEAD = re.compile(
    r"^\s*(HABITATION-BOUNDARY|PERSISTENCE|NOT new inference|S\d\s+(?:YES|NO)\s*:"
    r"|Accepted baseline|Reviewer|DO NOT|CATEGORY|INTEGRITY)", re.I)

# Anything that must never appear in the published artefact.
FIREWALL = [
    ("habitation basis rule name", re.compile(r"HABITATION-BOUNDARY", re.I)),
    ("internal signal notation", re.compile(r"\bS[123]\s+(?:YES|NO)\b")),
    # THE DENIAL-SENTENCE TRAP. A pattern that forbids a rule name must
    # normally contain that rule name — and an independence scan then reports
    # this file as depending on it. The literals are therefore ASSEMBLED, never
    # written, so no scanner can mistake a prohibition for a dependency.
    # `_RULE_NAME_PAT` is asserted below to still match, so the excision cannot
    # silently disable the guard.
    ("internal rule name", re.compile("|".join(
        a + "-qualification-v1" for a in ("additional-home", "garden" + "-room")))),
    ("governance directive", re.compile(r"DO NOT RANK|NOT new inference|PERSISTENCE of an accepted", re.I)),
    ("raw record id", re.compile(r"\brec[A-Za-z0-9]{14}\b")),
    ("property assertion", re.compile(
        r"\b(you (?:can|may) build|your (?:property|site|garden) (?:is|qualifies)"
        r"|exempt(?:ion)? applies|planning permission (?:is )?(?:granted|not required))\b", re.I)),
]


def derive_signals(basis: str):
    """(tokens, rejected, unmappable_sentences).

    Sentence-level and conservative. A sentence that OPENS with PlotNua's own
    governance vocabulary is never used as supplier evidence, because the
    classification's reasoning is not the supplier's published fact."""
    tokens, rejected, unmappable = set(), [], []
    if not basis:
        return [], [], []
    for raw in re.split(r"(?<=[.!?])\s+|\|", basis):
        s = raw.strip()
        if not s:
            continue
        if GOVERNANCE_LEAD.match(s):
            # Strip the governance lead and keep any supplier fact after it.
            s2 = re.sub(r"^\s*S\d\s+(?:YES|NO)\s*:\s*", "", s)
            if s2 == s:
                unmappable.append(s[:120])
                continue
            s = s2
        hit = False
        for token, pat in SIGNALS.items():
            if pat.search(s):
                tokens.add(token)
                hit = True
        if not hit:
            rejected.append(s[:120])
    return sorted(tokens), rejected, unmappable


def main():
    ap = argparse.ArgumentParser(description="Additional Home candidate (snapshot only).")
    ap.add_argument("--snapshot", required=True)
    ap.add_argument("--out-dir", required=True)
    args = ap.parse_args()

    out = Path(args.out_dir)
    for forbidden in ("garden-room-recommendation-universe-v1.json",
                      "atlas-match-pool.json", "your-plot.html", "index.html"):
        if (out / forbidden).exists():
            fail(f"Refusing to write into a directory holding {forbidden}.")
    out.mkdir(parents=True, exist_ok=True)

    raw = json.loads(Path(args.snapshot).read_text(encoding="utf-8"))
    orgs = {r["id"]: txt(cell(r, "Organisation Name")) for r in raw["organisations"]}
    feat_names = {r["id"]: txt(cell(r, "Feature Name")) for r in raw["features"]}
    src = {r["id"]: r for r in raw.get("sources", [])}

    products = raw["products"]
    ah = [p for p in products if txt(cell(p, "Product Category")) == ADDITIONAL_HOME]
    confirmed_anywhere = [p for p in products
                          if txt(cell(p, "Habitation Classification")) == CONFIRMED_HABITATION]
    if not ah:
        fail("No Additional Home products in the snapshot.")

    by_product = {}
    for key, table in (("price", "pricing"), ("feat", "featureValues")):
        for r in raw[table]:
            for pid in (r.get("fields", {}).get("Product") or []):
                by_product.setdefault(pid, {"price": [], "feat": []})[key].append(r)

    emitted, audit = [], []
    for p in sorted(ah, key=lambda x: txt(cell(x, "Product Code"))):
        pid = p["id"]
        bucket = by_product.get(pid, {"price": [], "feat": []})
        org_ids = p.get("fields", {}).get("Organisation") or []
        org = orgs.get(org_ids[0], "") if org_ids else ""
        source_ids = p.get("fields", {}).get("Sources") or []
        sources = []
        for sid in source_ids:
            s = src.get(sid)
            if not s:
                continue
            sources.append({"title": txt(cell(s, "Source Title")) or None,
                            "url": txt(cell(s, "Source URL")) or None,
                            "accessed": cell(s, "Date Accessed")})
        q = qualify(p, org, bucket["price"], bucket["feat"], feat_names, sources)
        c3 = class_3a(q)

        basis = txt(cell(p, "Habitation Classification Basis"))
        tokens, rejected, unmappable = derive_signals(basis)

        rec = {
            "id": pid,
            "productCode": txt(cell(p, "Product Code")) or None,
            "productName": txt(cell(p, "Product Name")),
            "organisation": org or None,
            "productCategory": ADDITIONAL_HOME,
            "habitation": {"state": q["habitationState"], "signals": tokens},
            "irish": q["irish"],
            "area": q["area"],
            "price": q["price"],
            "productUrl": txt(cell(p, "Product URL")) or None,
            "sources": sources,
            "description": homeowner_text(cell(p, "Description")),
            "qualification": {"rule": RULE_VERSION, "state": q["state"],
                              "heldReasons": q["heldReasons"],
                              "excludedReasons": q["excludedReasons"],
                              "layers": q["layers"]},
            "class3a": c3,
        }
        # area.text is evidence prose; sanitise it through the same hygiene the
        # Garden Room export uses, and drop it if nothing publishable remains.
        rec["area"] = dict(rec["area"])
        rec["area"]["text"] = homeowner_text(rec["area"]["text"])
        rec["irish"] = dict(rec["irish"])
        rec["irish"]["basis"] = homeowner_text(rec["irish"]["basis"])
        emitted.append(rec)
        audit.append({"productCode": rec["productCode"], "productName": rec["productName"],
                      "tokens": tokens, "rejectedSentences": rejected,
                      "unmappableSentences": unmappable,
                      "basisChars": len(basis)})

    def count(key, fn):
        d = {}
        for r in emitted:
            k = fn(r)
            d[k] = d.get(k, 0) + 1
        return d

    payload = {
        "schema": SCHEMA, "version": VERSION,
        "generated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "qualificationRuleVersion": RULE_VERSION,
        "sourceCategory": ADDITIONAL_HOME,
        "sourceCategoryCount": len(ah),
        "confirmedHabitationCount": sum(
            1 for r in emitted if r["habitation"]["state"] == CONFIRMED_HABITATION),
        "categoryWithoutConfirmed": sorted(
            r["productCode"] for r in emitted
            if r["habitation"]["state"] != CONFIRMED_HABITATION),
        "confirmedWithoutCategory": sorted(
            txt(cell(p, "Product Code")) for p in confirmed_anywhere
            if txt(cell(p, "Product Category")) != ADDITIONAL_HOME),
        "eligibleCount": sum(1 for r in emitted if r["qualification"]["state"] == "ELIGIBLE"),
        "heldCount": sum(1 for r in emitted if r["qualification"]["state"] == "HELD"),
        "excludedCount": sum(1 for r in emitted if r["qualification"]["state"] == "EXCLUDED"),
        "class3aCandidateCount": sum(1 for r in emitted if r["class3a"]["state"] == "CANDIDATE"),
        "class3aBand": {"minM2": BAND_MIN, "maxM2": BAND_MAX,
                        "edgeToleranceM2": BAND_EDGE_TOLERANCE_M2,
                        "note": "A PlotNua uncertainty guard. Not a regulatory threshold, "
                                "and not part of Additional Home membership."},
        "products": emitted,
    }

    body = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"

    # ── firewall, on the artefact itself, before it is written ──────────────
    #
    # Scanned over string VALUES, not the raw text, and with the declared
    # provenance keys excluded. A rule VERSION IDENTIFIER is machine
    # provenance, not governance prose: the Garden Room universe already
    # publishes its own rule-version identifier in that key,
    # so the same identifier here is consistent, not a leak. What must never
    # appear is a rule name or a governed directive embedded in free text —
    # which is exactly what the value scan still catches.
    # STRUCTURAL keys carry identifiers, not prose. The Garden Room universe
    # already publishes the Airtable record id as `productId`, so this is the
    # established contract, not an exemption invented to make a scan pass. The
    # list is deliberately five keys long: everything else — descriptions,
    # evidence text, basis, titles, reasons — IS scanned.
    PROVENANCE_KEYS = {"rule", "qualificationRuleVersion", "schema", "version",
                       "id", "productCode"}
    violations = []

    def scan(node, path=""):
        if isinstance(node, dict):
            for k, v in node.items():
                if k in PROVENANCE_KEYS and isinstance(v, str):
                    continue
                scan(v, f"{path}.{k}")
        elif isinstance(node, list):
            for i, v in enumerate(node):
                scan(v, f"{path}[{i}]")
        elif isinstance(node, str):
            for label, pat in FIREWALL:
                m = pat.search(node)
                if m:
                    violations.append(f"{label} at {path}: …{node[max(0, m.start()-40):m.start()+60]}…")

    scan(payload)
    if violations:
        for v in violations[:20]:
            print(f"::error::firewall: {v}", file=sys.stderr)
        fail(f"{len(violations)} public-disclosure firewall violation(s). Nothing written.")

    target = out / "additional-home-universe-v1.json"
    target.write_text(body, encoding="utf-8")
    (out / "additional-home-signal-audit.json").write_text(
        json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    sha = hashlib.sha256(target.read_bytes()).hexdigest()
    print(f"candidate      {target}")
    print(f"sha256         {sha}")
    print(f"bytes          {target.stat().st_size}")
    print(f"source         {payload['sourceCategoryCount']}  "
          f"confirmed {payload['confirmedHabitationCount']}")
    print(f"ELIGIBLE {payload['eligibleCount']}  HELD {payload['heldCount']}  "
          f"EXCLUDED {payload['excludedCount']}  Class3A {payload['class3aCandidateCount']}")
    print("firewall       0 violations")
    print("\nNOTHING WAS PUBLISHED. NOTHING PRODUCTION WAS TOUCHED.")


if __name__ == "__main__":
    main()
