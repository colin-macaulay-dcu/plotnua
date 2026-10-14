#!/usr/bin/env python3
"""PlotNua — generate_wellness_universe.py

Builds wellness-universe-v1.json — the published eligibility file for Atlas
Product Category "Wellness / Sauna" (DISC-001 Garden Retreat: saunas, hot tubs,
cold plunges) — from a frozen Atlas snapshot.

THE THIRD UNIVERSE, BUILT THE SAME WAY AS THE SECOND. Founder decision, 14 Oct
2026 ("OGNYX public integration — PROCEED"): reuse PlotNua's existing
publication architecture, no supplier-specific system. So this is the
Additional Home pattern, narrowed:

  * reads a snapshot only; no Airtable client, cannot write production;
  * the PUBLICATION GATE is the Additional Home generator's own
    publication_hold(), imported rather than copied, so there is one rule;
    every record carries publicVisibility and the artefact declares the gate,
    so readers fail closed;
  * qualification is EVIDENCE ONLY and never re-decides permission:
      EXCLUDED  no organisation, no product URL, or no source;
      HELD      Atlas records a contradiction or evidence gap (Standards
                carries BLOCKED) -- the supplier's own page disagrees with
                itself, so PlotNua shows neither figure;
      ELIGIBLE  otherwise.
    A product is PUBLIC only if it is ELIGIBLE and its organisation derives
    PUBLISHABLE. Nothing is published "automatically": a new wellness
    supplier with no rights record holds (publication-record-missing).

PUBLIC-DISCLOSURE FIREWALL. Description, Notes, Standards prose and Habitation
basis are read and NEVER exported. What reaches the artefact is identity,
the Atlas product type, a verified 'from' price with its basis, and closed
state tokens. No health, VAT, delivery, installation or lead-time statement is
ever emitted; a price whose VAT position is unknown says so in its basis.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from atlas_common import cell, links, txt, fail          # noqa: E402
from generate_additional_home_universe import (           # noqa: E402
    publication_hold, NO_RECORD_HOLD)

SCHEMA = "plotnua.wellness-universe"
VERSION = "1.0.0"
RULE_VERSION = "wellness-qualification-v1"
CATEGORY = "Wellness / Sauna"
PRICE_BASIS = {
    "Unknown": "Published 'from' price for the basic set. The supplier does not "
               "state whether it includes VAT.",
    "Yes": "Published 'from' price for the basic set, including VAT.",
    "No": "Published 'from' price for the basic set, excluding VAT.",
}
# The closed set of fields a public record may carry.
PUBLIC_FIELDS = {"id", "productCode", "productName", "organisation",
                 "productCategory", "productType", "price", "irish",
                 "qualification", "publicVisibility", "holdReason"}


def price_of(rows):
    """VERIFIED_NUMERIC_PRICE only from exactly one verified EUR row."""
    live = [r for r in rows if txt(cell(r, "Status")) == "Verified"]
    if len(live) != 1:
        return {"state": "PRICE_NOT_ESTABLISHED"}
    r = live[0]
    amt = cell(r, "Base Price")
    if not isinstance(amt, (int, float)) or amt <= 0 or txt(cell(r, "Currency")) != "EUR":
        return {"state": "PRICE_NOT_ESTABLISHED"}
    vat = txt(cell(r, "Price Includes VAT")) or "Unknown"
    return {"state": "VERIFIED_NUMERIC_PRICE", "amount": amt, "currency": "EUR",
            "type": txt(cell(r, "Price Type")) or None,
            "basis": PRICE_BASIS.get(vat, PRICE_BASIS["Unknown"])}


def qualify(p, org, nprice, navail):
    excluded, held = [], []
    if not org:
        excluded.append("no-organisation")
    if not txt(cell(p, "Product URL")):
        excluded.append("no-product-url")
    if not links(p, "Sources"):
        excluded.append("no-source")
    if not nprice or not navail:
        held.append("evidence-incomplete")
    if "BLOCKED" in txt(cell(p, "Standards")).upper():
        held.append("recorded-contradiction")
    state = "EXCLUDED" if excluded else ("HELD" if held else "ELIGIBLE")
    return {"rule": RULE_VERSION, "state": state,
            "heldReasons": held, "excludedReasons": excluded}


def main():
    ap = argparse.ArgumentParser(description="Wellness / Sauna universe (snapshot only).")
    ap.add_argument("--snapshot", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    raw_bytes = Path(args.snapshot).read_bytes()
    raw = json.loads(raw_bytes)
    orgs = {r["id"]: txt(cell(r, "Organisation Name")) for r in raw["organisations"]}
    by_prod = lambda rows: {pid: [r for r in rows if pid in links(r, "Product")]
                            for pid in {x for r in rows for x in links(r, "Product")}}
    pricing, avail = by_prod(raw.get("pricing", [])), by_prod(raw.get("availability", []))

    src = [p for p in raw["products"] if txt(cell(p, "Product Category")) == CATEGORY]
    if not src:
        fail("No product carries Product Category %r; refusing to write an empty universe." % CATEGORY)

    emitted = []
    for p in src:
        oid = (links(p, "Organisation") or [None])[0]
        org = orgs.get(oid) if oid else None
        prs = pricing.get(p["id"], [])
        q = qualify(p, org, len(prs), len(avail.get(p["id"], [])))
        hold = publication_hold(org) if org else NO_RECORD_HOLD
        rec = {
            "id": p["id"],
            "productCode": txt(cell(p, "Product Code")) or None,
            "productName": txt(cell(p, "Product Name")),
            "organisation": org,
            "productCategory": CATEGORY,
            "productType": txt(cell(p, "Product Type")) or None,
            "price": price_of(prs),
            # Irish availability is a per-product Atlas feature value. None is
            # recorded for these products, so it is UNCONFIRMED -- never
            # inferred from where a company is registered.
            "irish": {"state": "UNCONFIRMED"},
            "qualification": q,
            "publicVisibility": "HOLD" if hold else "PUBLISHABLE",
            "holdReason": hold,
        }
        if set(rec) != PUBLIC_FIELDS:
            fail("a record carries a field outside the public set")
        emitted.append(rec)

    emitted.sort(key=lambda r: (r["organisation"] or "", r["productName"].lower()))
    public = [r for r in emitted if r["qualification"]["state"] == "ELIGIBLE"
              and r["publicVisibility"] == "PUBLISHABLE"]
    count = lambda s: sum(1 for r in emitted if r["qualification"]["state"] == s)
    payload = {
        "schema": SCHEMA, "version": VERSION,
        "generated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "qualificationRuleVersion": RULE_VERSION,
        "publicationGate": {
            "version": "supplier-publication-gate-v1",
            "rule": ("public visibility is derived from permission state, "
                     "listing-review state and asset approval by the Additional "
                     "Home generator's publication_hold(); a product is public "
                     "only when ELIGIBLE and PUBLISHABLE."),
            "heldOrganisations": sorted({r["organisation"] for r in emitted
                                         if r["publicVisibility"] == "HOLD" and r["organisation"]}),
        },
        "snapshotSha256": hashlib.sha256(raw_bytes).hexdigest(),
        "snapshotScope": raw.get("source", ""),
        "sourceCategory": CATEGORY,
        "sourceCategoryCount": len(src),
        # eligibleCount counts what a homeowner may see: ELIGIBLE AND PUBLISHABLE.
        "eligibleCount": len(public),
        "organisationCount": len({r["organisation"] for r in public}),
        "heldCount": count("HELD"),
        "excludedCount": count("EXCLUDED"),
        "gateHeldCount": sum(1 for r in emitted if r["qualification"]["state"] == "ELIGIBLE"
                             and r["publicVisibility"] != "PUBLISHABLE"),
        "products": emitted,
    }
    out = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    for bad in ("health", "therapeutic", "vat included", "including vat",
                "free delivery", "installation included", "lead time"):
        if bad in json.dumps([{k: v for k, v in r.items() if k != "price"} for r in emitted]).lower():
            fail("the firewall leaked %r into a public record" % bad)
    Path(args.out).write_text(out, encoding="utf-8")
    print("WELLNESS universe: %d source, %d public (ELIGIBLE and PUBLISHABLE), "
          "%d held on evidence, %d excluded, %d held by the gate"
          % (len(src), payload["eligibleCount"], payload["heldCount"],
             payload["excludedCount"], payload["gateHeldCount"]))


if __name__ == "__main__":
    main()
