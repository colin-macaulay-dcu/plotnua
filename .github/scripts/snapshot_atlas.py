#!/usr/bin/env python3
"""PlotNua — snapshot_atlas.py

SOURCE ACQUISITION ONLY. This script reads Atlas and writes one frozen JSON
snapshot. It does nothing else, and it must never be made to do anything else.

WHY IT EXISTS.
  The first Gate S1 snapshot was produced by generate_garden_room_universe.py,
  which declares its reads explicitly in PRODUCT_FIELDS. That explicitness is
  correct and is not being weakened — but it means the snapshot inherited the
  Garden Room field list and carried no habitation fields at all. Additional
  Home qualification cannot run without them.

  The wrong fix would be to add habitation fields to the Garden Room generator
  so that a snapshot happens to contain them. That would widen a production
  export contract to serve an unrelated acquisition need, and the Garden Room
  byte-identity proof would have to be re-established for no benefit. This
  script exists so that does not happen.

WHAT IT IS NOT.
  Not a generator. It contains no qualification, no Additional Home universe,
  no Class 3A logic, no homeowner presentation, no ranking and no public
  artefact. It does not write Airtable, does not touch production, does not
  commit, push or deploy. If a future change would add any of those, the
  change belongs in a generator, not here.

FAIL-CLOSED.
  Every field this snapshot must carry is declared below as REQUIRED. After
  the read, each one is checked. A required field that never appears in any
  record means the field was renamed, mistyped or not requested — the script
  fails and writes nothing rather than handing on a partial snapshot that
  would silently produce a wrong answer downstream.

THE SNAPSHOT IS INTERNAL GOVERNANCE DATA.
  It carries Habitation Classification Basis, Notes and research prose. It is
  never committed, never deployed and never served from plotnua.ie.

THE TOKEN.
  Read from the environment only, exactly as the Garden Room generator does.
  Never echoed, never written to the snapshot, never written to the manifest.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path

from atlas_common import (
    T_PRODUCTS, T_PRICING, T_AVAIL, T_FEATVALS, T_FEATURES, T_ORGS,
    fail, fetch_all, cell, txt,
)

# The Sources table is not read by the Garden Room generator, so its id is not
# in atlas_common. Declared here, where it is used.
T_SOURCES = "tblgrb1viLZytKXr9"

ADDITIONAL_HOME = "Additional Home"

# ── THE FIELDS, AND WHY ──────────────────────────────────────────────────────
# Every entry is justified against Implementation Brief v1 and the S3 evidence
# the founder requires. Nothing is requested "in case".
PRODUCT_FIELDS = [
    # identity and source membership — Brief §3, §4
    "Product Name", "Product Code", "Product Type", "Product Category",
    "Status", "Verification Status", "Organisation", "Brand",
    # habitation admission and public-safe signal derivation — Brief §5, §6.2
    "Habitation Classification", "Habitation Classification Basis",
    # evidence sufficiency — Brief §6.2 layer 4
    "Product URL", "    Sources", "Sources", "Description", "Notes",
    # provenance freshness — S3 "provenance coverage"
    "    Last Reviewed",
    # carried so the independence tests can PROVE these were available and
    # deliberately not used by additional-home-qualification-v1 (Brief §6, ruling 7)
    "Atlas Product Certification Audit v1", "Results Eligibility v1",
    "Standards",
]
REQUIRED_PRODUCT_FIELDS = [
    "Product Name", "Product Category",
    "Habitation Classification", "Habitation Classification Basis",
    "Organisation",
]

PRICING_FIELDS = [
    # Q2: verified numeric price vs evidenced POA/quote vs PRICE NOT PUBLISHED.
    # "Price Type" is the field that evidences a quote-only position; without
    # it the three states collapse into two and UNKNOWN becomes POA by
    # inference, which the ruling forbids.
    "Product", "Base Price", "Price From", "Price To", "Currency",
    "Price Type", "Price Includes VAT", "Status", "Primary Price",
    "Evidence Scope", "Known Exclusions", "Last Price Check", "Sources",
]
REQUIRED_PRICING_FIELDS = ["Product", "Price Type", "Status"]

AVAIL_FIELDS = ["Product", "Availability", "Status", "Evidence Scope",
                "Availability URL", "Notes"]
REQUIRED_AVAIL_FIELDS = ["Product", "Availability"]

FEATVAL_FIELDS = [
    # Irish availability (Value Text + Confirmation State), floor area
    # (Value Number + Unit) and measurement basis (Value Text prose) all live
    # here. "Sources" resolves per-fact provenance — Brief §4 sources[].
    "Product", "Feature", "Value Text", "Value Number", "Unit",
    "Value Boolean", "Confirmation State", "Evidence Scope", "Status",
    "Sources", "Notes", "Source Notes",
]
REQUIRED_FEATVAL_FIELDS = ["Product", "Feature", "Value Text",
                           "Confirmation State"]

FEATURE_FIELDS = ["Feature Name", "Feature Code", "Feature Group", "Data Type"]
REQUIRED_FEATURE_FIELDS = ["Feature Name"]

ORG_FIELDS = ["Organisation Name", "Organisation Type", "Website",
              "Headquarters", "Sources", "Last Reviewed "]
REQUIRED_ORG_FIELDS = ["Organisation Name"]

SOURCE_FIELDS = ["Source Title", "Source URL", "Source Type", "Date Accessed",
                 "Last Verified", "Evidence Quality", "Product",
                 "Product Feature Values", "Product Pricing", "Organisation"]
REQUIRED_SOURCE_FIELDS = ["Source Title"]

TABLES = [
    ("products",      T_PRODUCTS, PRODUCT_FIELDS, REQUIRED_PRODUCT_FIELDS),
    ("pricing",       T_PRICING,  PRICING_FIELDS, REQUIRED_PRICING_FIELDS),
    ("availability",  T_AVAIL,    AVAIL_FIELDS,   REQUIRED_AVAIL_FIELDS),
    ("featureValues", T_FEATVALS, FEATVAL_FIELDS, REQUIRED_FEATVAL_FIELDS),
    ("features",      T_FEATURES, FEATURE_FIELDS, REQUIRED_FEATURE_FIELDS),
    ("organisations", T_ORGS,     ORG_FIELDS,     REQUIRED_ORG_FIELDS),
    ("sources",       T_SOURCES,  SOURCE_FIELDS,  REQUIRED_SOURCE_FIELDS),
]

# The six governed habitation states. Counted in the manifest so the founder
# can see the snapshot is usable without any Basis prose being printed.
HABITATION_STATES = [
    "CONFIRMED RESIDENTIAL HABITATION",
    "PROBABLE — MORE EVIDENCE REQUIRED",
    "ANCILLARY / NON-DWELLING",
    "AMBIGUOUS",
    "CONTRADICTED",
    "UNKNOWN / NOT YET ASSESSED",
]


def coverage(rows, field):
    """How many records actually carry this field. Airtable omits empty
    fields, so this is a presence count, never a truth claim."""
    return sum(1 for r in rows if field in r.get("fields", {}))


def main():
    ap = argparse.ArgumentParser(
        description="Read-only Atlas snapshot for Additional Home Steps 2-3.")
    ap.add_argument("--out", required=True, help="Snapshot JSON path.")
    ap.add_argument("--manifest", required=True, help="Structural manifest path.")
    args = ap.parse_args()

    out = Path(args.out)
    for forbidden in ("garden-room-recommendation-universe-v1.json",
                      "additional-home-universe-v1.json",
                      "atlas-match-pool.json", "your-plot.html"):
        if (out.parent / forbidden).exists():
            fail(f"Refusing to write into a directory holding {forbidden}.")

    token = os.environ.get("AIRTABLE_TOKEN")
    if not token:
        fail("AIRTABLE_TOKEN is not set. This script reads it from the "
             "environment only, and never accepts a credential by any other route.")

    raw, problems, lines = {}, [], []
    for name, table, fields, required in TABLES:
        print(f"Reading {name}…")
        try:
            rows = fetch_all(token, table, fields)
        except Exception as e:
            fail(f"Atlas read failed for {name}: {e}")
        raw[name] = rows
        lines.append(f"{name}: {len(rows)} records")
        for f in fields:
            c = coverage(rows, f)
            flag = "REQUIRED" if f in required else "        "
            lines.append(f"    {flag}  {c:>6} / {len(rows)}  {f!r}")
            if f in required and c == 0:
                problems.append(
                    f"{name}.{f!r} was requested but appears in NO record. "
                    "The field is renamed, mistyped, or not readable.")

    # ── the checks that decide whether this snapshot is usable at all ────────
    prods = raw["products"]
    ah = [p for p in prods
          if txt(cell(p, "Product Category")) == ADDITIONAL_HOME]
    if not ah:
        problems.append(f"No product carries Product Category == {ADDITIONAL_HOME!r}. "
                        "Either the choice was renamed or the read is wrong.")

    hab_present = sum(1 for p in ah if "Habitation Classification" in p.get("fields", {}))
    if hab_present == 0:
        problems.append("No Additional Home product carries Habitation "
                        "Classification. Steps 2-3 cannot run on this snapshot.")

    states = {s: 0 for s in HABITATION_STATES}
    unrecognised = 0
    for p in prods:
        v = txt(cell(p, "Habitation Classification"))
        if not v:
            continue
        if v in states:
            states[v] += 1
        else:
            unrecognised += 1
    if unrecognised:
        problems.append(f"{unrecognised} product(s) carry a Habitation "
                        "Classification value outside the six governed states.")

    if problems:
        for p in problems:
            print(f"::error::{p}", file=sys.stderr)
        fail("Required governed fields are missing or invalid. "
             "No snapshot written — a partial snapshot would produce a wrong "
             "answer downstream and look like a right one.")

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(raw), encoding="utf-8")
    sha = hashlib.sha256(out.read_bytes()).hexdigest()

    # ── the manifest: structure and counts only, never governed prose ───────
    man = [
        "PLOTNUA — COMPLETE ATLAS SNAPSHOT MANIFEST",
        "For Additional Home Implementation Steps 2-3.",
        "",
        f"generated (UTC)   {time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())}",
        f"python            {sys.version.split()[0]}",
        f"snapshot sha256   {sha}",
        f"snapshot bytes    {out.stat().st_size}",
        "",
        "TABLES AND FIELD COVERAGE",
        "  (coverage is how many records CARRY the field; Airtable omits empty",
        "   fields, so a low count is data sparsity, never a failed read.)",
        "",
    ] + ["  " + l for l in lines] + [
        "",
        "ADDITIONAL HOME SOURCE POPULATION",
        f"  Product Category == 'Additional Home'     {len(ah)}",
        f"  of those, carrying Habitation Classification  {hab_present}",
        "",
        "GOVERNED HABITATION STATES ACROSS ALL PRODUCTS (counts only)",
    ] + [f"  {c:>5}  {s}" for s, c in states.items()] + [
        "",
        "NO HABITATION CLASSIFICATION BASIS TEXT IS PRINTED IN THIS MANIFEST.",
        "",
        "THE SNAPSHOT CONTAINS INTERNAL ATLAS GOVERNANCE MATERIAL.",
        "Do not commit it. Do not deploy it. Do not serve it from plotnua.ie.",
    ]
    Path(args.manifest).write_text("\n".join(man) + "\n", encoding="utf-8")
    print("\n".join(man))
    print("\nNOTHING WAS WRITTEN TO AIRTABLE. NOTHING PRODUCTION WAS TOUCHED.")


if __name__ == "__main__":
    main()
