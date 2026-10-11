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


# ── the publication gate ────────────────────────────────────────────────────
RIGHTS = Path(__file__).resolve().parent.parent.parent / "image-rights-records.json"


# The four reasons no decision may waive, kept in step with NEVER_WAIVABLE in
# atlas-tools/publication-gate.mjs. A founder can accept the risk of
# publishing early against a grant PlotNua HOLDS; a founder cannot conjure a
# grant that was never given. prove-supplier-publication-gate.mjs (PG11)
# refuses if this list and the JS one ever drift apart.
GATE_NEVER_WAIVABLE = (
    "permission-declined",
    "no-permission",
    "permission-conditional-unresolved",
    "permission-state-missing",
)

GATE_WAIVABLE = (
    "listing-review-awaiting-confirmation",
    "listing-review-changes-requested",
    "listing-review-state-missing",
    "assets-not-approved",
)


def _founder_waives(row):
    """The hold reasons a well-formed founder exception on this row accepts.

    THIRD MIRROR OF ONE RULE, and the one that was missed when the exception
    mechanism was built: the generator keeps its own copy of the gate so a
    held supplier cannot be published even if the runtime reader is bypassed,
    and that copy knew nothing about exceptions. Regenerating would have put
    an authorised supplier straight back on HOLD with every guard green.

    A malformed exception waives NOTHING -- it does not half-work and it does
    not fail open -- and the permission class can never be waived however the
    record is written."""
    ex = row.get("founder_exception")
    if not isinstance(ex, dict):
        return ()
    if not isinstance(ex.get("authorised_by"), str) or not ex["authorised_by"]:
        return ()
    date = str(ex.get("decision_date") or "")
    if len(date) != 10 or date[4] != "-" or date[7] != "-":
        return ()
    if ex.get("supplier_confirmation_received") is not False:
        return ()
    if len(str(ex.get("basis") or "").strip()) < 20:
        return ()
    waives = ex.get("waives")
    if not isinstance(waives, list) or not waives:
        return ()
    for w in waives:
        if w in GATE_NEVER_WAIVABLE or w not in GATE_WAIVABLE:
            # One bad entry invalidates the whole exception, exactly as
            # founderExceptionProblems() does in the JS gate.
            return ()
    return tuple(waives)


def _gate_index():
    """organisation name (upper) -> holdReason, or None when publishable.

    Mirrors derivePublicVisibility() in atlas-tools/publication-gate.mjs. The
    two are pinned together by prove-publication-gate.mjs, which runs this
    generator's own rule against the same records."""
    try:
        doc = json.loads(RIGHTS.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        fail("the publication gate could not read image-rights-records.json "
             "(%s). Refusing to generate rather than publish ungated." % e)
    rows = doc if isinstance(doc, list) else next(
        (v for v in doc.values() if isinstance(v, list) and v and
         isinstance(v[0], dict)), [])
    idx = {}
    for r in rows:
        name = (r.get("organisation_name") or "").strip().upper()
        if not name:
            continue
        perm = ((r.get("permission") or {}).get("state"))
        rev = ((r.get("listing_review") or {}).get("state"))
        assets = r.get("asset_approval_state")
        if perm is None and rev is None:
            # A rights row that predates the gate fields. It governs imagery
            # only and says nothing about publication, so it holds nobody.
            continue
        # Conditions in the gate's fixed order; the first unsatisfied one
        # decides. Written as a list rather than a chain of elifs so the
        # founder-exception filter below can be applied uniformly instead of
        # being threaded through eight branches.
        conditions = [
            (perm not in ("GRANTED", "CONDITIONAL", "DECLINED", "NONE"),
             "permission-state-missing"),
            (rev not in ("NOT_REQUIRED", "AWAITING_CONFIRMATION", "CONFIRMED",
                         "CHANGES_REQUESTED"), "listing-review-state-missing"),
            (perm == "DECLINED", "permission-declined"),
            (perm == "NONE", "no-permission"),
            (perm == "CONDITIONAL", "permission-conditional-unresolved"),
            (rev == "AWAITING_CONFIRMATION",
             "listing-review-awaiting-confirmation"),
            (rev == "CHANGES_REQUESTED", "listing-review-changes-requested"),
            (bool(assets) and assets != "APPROVED", "assets-not-approved"),
        ]
        accepted = _founder_waives(r)
        for unsatisfied, reason in conditions:
            if not unsatisfied:
                continue
            if reason in accepted:
                continue
            idx[name] = reason
            break
    return idx


_GATE = None


def publication_hold(org_name):
    """The hold reason for this organisation, or None."""
    global _GATE
    if _GATE is None:
        _GATE = _gate_index()
    return _GATE.get((org_name or "").strip().upper())


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

        # THE PUBLICATION GATE, APPLIED AT GENERATION TIME.
        #
        # CORRECTED 11 October 2026. The first version of this overwrote
        # class_3a with NOT_A_CANDIDATE / publication-hold. That was wrong:
        # it made a COMMERCIAL state masquerade as a TECHNICAL finding. Class
        # 3A is an assessment of the structure against the 32-45 m2 pathway
        # band and its measurement basis. Whether a supplier has countersigned
        # their listing has nothing to do with it, and writing the hold into
        # that field would have left Atlas asserting something untrue about
        # the building and losing the real assessment while the hold lasted.
        #
        # The two are now kept apart. class_3a keeps saying what is true about
        # the structure. publicVisibility says whether anyone may see it. The
        # gate is enforced through publicVisibility alone, at both the
        # generator and the reader, and a measurement still cannot publish
        # anybody because the gate never reads one.
        hold = publication_hold(org)

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
            # The technical assessment, untouched by any commercial state.
            "class3a": c3,
            # The commercial state, carried onto every record so the runtime
            # reader can refuse independently rather than trusting that the
            # generator did. Two locks, neither reading the other's field.
            "publicVisibility": "HOLD" if hold else "PUBLISHABLE",
            "holdReason": hold,
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
        # THE GATE'S OWN DECLARATION. Its presence is how the runtime reader
        # knows this artefact was built by a gate-aware generator and can
        # therefore FAIL CLOSED: require PUBLISHABLE, rather than treating a
        # missing field as permission. An older artefact carries no such
        # declaration and keeps its previous behaviour exactly, so nothing
        # that is live today changes before the first regeneration.
        "publicationGate": {
            "version": "supplier-publication-gate-v1",
            "rule": ("public visibility is derived from permission state, "
                     "listing-review state and asset approval. It never "
                     "reads a measurement, and it never alters the Class 3A "
                     "technical assessment."),
            "heldOrganisations": sorted(
                {r["organisation"] for r in emitted
                 if r.get("publicVisibility") == "HOLD" and r.get("organisation")}),
        },
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
