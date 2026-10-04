#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GENERATE THE PUBLICATION-RIGHTS MANIFEST.

image-rights-manifest.json said, in its own governance note, that it was
"Produced by .github/scripts/generate_image_rights_manifest.py". That script
did not exist. The manifest was hand-maintained while claiming not to be,
which is the kind of gap that only shows up when someone tries to follow the
process -- as happened when the Power Sheds grant had to be reconciled.

So here it is, and the process is now real:

    image-rights-records.json          the canonical rights records
        -> generate_image_rights_manifest.py
            -> image-rights-manifest.json   the gate's input
                -> atlas-tools/validate-image-rights.js

WHAT THIS DOES, AND DELIBERATELY DOES NOT DO.

It VALIDATES and STAMPS. It does not interpret, infer, upgrade or soften
anything. Every permission outcome must be spelled exactly as the gate spells
it; an outcome the gate would not recognise is refused HERE rather than being
written into a manifest that then fails in CI with a less useful message.

It does not reach Airtable. Atlas is the source of record, but a CI job
holding a token that decides whether an image may be published is a larger
blast radius than this needs. A human reads Atlas, writes the record, and
commits it with the Atlas id attached so the two can be checked against each
other later.

THE SCOPED DELIVERY HOST RULE, which is the reason this had to exist now.
A supplier whose site runs on Shopify, Squarespace or Wix serves their own
photographs from a third-party CDN. "Their website" and "their domain" stop
being the same string. A delivery host may therefore be declared, but ONLY
with a path prefix narrow enough to be that supplier's alone. A bare CDN host
is refused: cdn.shopify.com without a prefix would authorise every Shopify
store on the internet, which is not what any supplier granted.

THE DATE STAMP IS NOT DRIFT. The manifest carries a 'generated' date, and a
regeneration stamps today. --check therefore compares the committed manifest
against a fresh one re-serialised with the COMMITTED stamp, so a manifest whose
rights are correct does not fail for being a day old. Everything else is still
compared byte for byte -- key order, indentation, every row and field. The
stamp must still be real: a missing, malformed or future-dated stamp is
refused, because freshness is enforced from that date by
atlas-tools/validate-image-rights.js (--max-age-days 30), and a manifest that
lied about its own age would defeat it.

Run:  python3 .github/scripts/generate_image_rights_manifest.py
      python3 .github/scripts/generate_image_rights_manifest.py --check
"""

import collections
import datetime
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent.parent
RECORDS = REPO / "image-rights-records.json"
MANIFEST = REPO / "image-rights-manifest.json"

CHECK_ONLY = "--check" in sys.argv

# THE SAME VOCABULARY THE GATE ENFORCES, spelled out here too. Duplicated on
# purpose: if the two ever drift, the generator refuses rather than emitting a
# manifest the gate will reject for a reason nobody can see from the record.
LIVE_GRANTS = {
    "Granted — Founder Confirmed",
    "Granted with Conditions — Founder Confirmed",
    "Granted — Supplier Confirmed (one-click)",
}
KNOWN_NON_GRANTS = {
    "Unknown — Awaiting Reply",
    "Unclear — Founder Review Required",
    "Declined — Founder Confirmed",
    "Withdrawn / Superseded",
}

# Field order in the emitted manifest. Stable so a regeneration produces a
# readable diff rather than a reshuffle.
ORDER = [
    "organisation_record", "organisation_code", "organisation_name",
    "permission_outcome", "permitted_domain", "permitted_delivery_hosts",
    "required_credit", "withdrawal_effective_at", "evidence", "conditions",
    "note", "atlas_permission_record", "atlas_permission_ref",
    "permission_date",
]


def die(msg):
    print("ABORT: " + msg)
    sys.exit(1)


def check_record(i, r):
    """Every refusal here is a refusal to publish a manifest that would let
    something through for a reason nobody wrote down."""
    who = r.get("organisation_name") or r.get("organisation_record") or ("record %d" % i)

    if not r.get("organisation_record"):
        die(who + ": no organisation_record; the gate keys on it")

    outcome = r.get("permission_outcome")
    if outcome not in LIVE_GRANTS and outcome not in KNOWN_NON_GRANTS:
        die(who + ": permission_outcome " + json.dumps(outcome, ensure_ascii=False)
            + " is not in the gate's vocabulary. Spell it exactly, or add it to "
              "the gate first and understand what you are widening.")

    live = outcome in LIVE_GRANTS and not r.get("withdrawal_effective_at")

    # A LIVE GRANT MUST SAY WHERE IT CAME FROM. A grant with no evidence and no
    # Atlas id is indistinguishable from someone's recollection.
    if live:
        if not r.get("permitted_domain"):
            die(who + ": a live grant with no permitted_domain would cover every "
                       "host on the internet")
        if not r.get("evidence"):
            die(who + ": a live grant with no evidence field")
        if not r.get("atlas_permission_record"):
            die(who + ": a live grant with no atlas_permission_record; Atlas is "
                       "the source of record and the manifest must point back at it")

    # THE SCOPED DELIVERY HOSTS.
    for d in r.get("permitted_delivery_hosts") or []:
        if not isinstance(d, dict):
            die(who + ": permitted_delivery_hosts entries must be objects")
        host = (d.get("host") or "").strip().lower()
        prefix = (d.get("path_prefix") or "").strip()
        if not host:
            die(who + ": a delivery host with no host")
        if not prefix:
            die(who + ": delivery host " + host + " has NO path_prefix. A bare "
                       "CDN host would authorise every other customer of that CDN. "
                       "Give the prefix that is this supplier's alone, or drop it.")
        if not prefix.startswith("/"):
            die(who + ": delivery host " + host + " path_prefix must start with /")
        if prefix == "/":
            die(who + ": delivery host " + host + " path_prefix '/' is the whole "
                       "CDN; that is not a scope")
        if not d.get("why"):
            die(who + ": delivery host " + host + " has no 'why'. If it cannot be "
                       "explained in a sentence it should not be in the manifest.")

    # A CONDITION THAT IS NOT ENFORCEABLE IS NOT A CONDITION. Where the record
    # states conditions in prose, at least one of them has to be the credit the
    # gate can actually check.
    if live and r.get("conditions") and not r.get("required_credit"):
        die(who + ": conditions are recorded but no required_credit, so the gate "
                   "has nothing to enforce. If attribution is a condition, name it.")


def stamp_of(current):
    """The committed manifest's own 'generated' date, or (None, reason).

    The date is exempt from the drift comparison, so it has to be checked on
    its own terms instead. A stamp that is missing, malformed, or dated in the
    future would defeat the staleness rule in validate-image-rights.js, which
    computes the manifest's age FROM THIS FIELD -- a manifest stamped next year
    would read as perpetually fresh. Each of those is refused here, where the
    message can say what to do, rather than in CI.
    """
    if not current.strip():
        return None, "no committed manifest to compare against"
    try:
        stamp = json.loads(current).get("generated")
    except ValueError:
        return None, "the committed manifest is not readable JSON"
    if not isinstance(stamp, str) or not stamp:
        return None, "the committed manifest has no generated date"
    try:
        when = datetime.date.fromisoformat(stamp)
    except ValueError:
        return None, "the generated date is not a plain ISO date: " + stamp
    if when > datetime.date.today():
        return None, ("the generated date is in the future: " + stamp
                      + ". A manifest cannot be stamped ahead of itself; that "
                      + "would read as perpetually fresh.")
    return stamp, None


def main():
    if not RECORDS.exists():
        die("image-rights-records.json not found; it is the input")
    src = json.loads(RECORDS.read_text(encoding="utf-8"))
    records = src.get("records")
    if not isinstance(records, list) or not records:
        die("image-rights-records.json has no records array")

    seen = set()
    for i, r in enumerate(records):
        check_record(i, r)
        org = r["organisation_record"]
        if org in seen:
            die("two records for organisation " + org + "; the gate would take "
                "the stricter one, but the ambiguity should not exist")
        seen.add(org)

    rows = []
    for r in records:
        row = collections.OrderedDict()
        for k in ORDER:
            if k in r and r[k] not in (None, "", [], {}):
                row[k] = r[k]
        for k in r:                       # anything new, kept rather than dropped
            if k not in row and r[k] not in (None, "", [], {}):
                row[k] = r[k]
        rows.append(row)

    live = [r for r in records
            if r["permission_outcome"] in LIVE_GRANTS
            and not r.get("withdrawal_effective_at")]

    out = collections.OrderedDict([
        ("schema", "plotnua.image-rights.manifest.v1"),
        ("generated", datetime.date.today().isoformat()),
        ("source_of_record", src.get("source_of_record", "")),
        ("governance",
         "GENERATED, NOT HAND-EDITED. Produced by "
         ".github/scripts/generate_image_rights_manifest.py from "
         "image-rights-records.json, which carries the canonical rights "
         "records and the Atlas id behind each one. It is the input to "
         "atlas-tools/validate-image-rights.js, which runs in the publish "
         "path and refuses to publish any supplier image without a live grant "
         "here. Regenerate and commit it in the same act as recording a grant "
         "or a withdrawal: the gate refuses a manifest older than 30 days "
         "precisely so a stale one cannot quietly authorise anything."),
        ("reality_note",
         "PlotNua publishes supplier imagery for %d supplier(s) under a live "
         "grant: %s. Every other supplier row in Image Permission Outreach "
         "reads Unknown — Awaiting Reply, and no other supplier image is "
         "published anywhere on the site."
         % (len(live), ", ".join(r["organisation_name"] for r in live))),
        ("reconciliation",
         "Every row carries the Atlas record id it reflects, so a "
         "disagreement between this manifest and Atlas is visible rather than "
         "silent. Generated from image-rights-records.json; edit that file, "
         "never this one."),
        ("rows", rows),
    ])

    text = json.dumps(out, indent=2, ensure_ascii=False) + "\n"
    if CHECK_ONLY:
        current = MANIFEST.read_text(encoding="utf-8") if MANIFEST.exists() else ""
        print("VALIDATED %d record(s), %d live grant(s)" % (len(records), len(live)))

        # Compare against the committed manifest re-stamped with ITS OWN date,
        # so a correct manifest does not fail merely for being a day old. The
        # stamp is the ONLY exemption, and it must be a real past date: see
        # stamp_of() for why.
        stamp, why = stamp_of(current)
        if stamp is None:
            print("manifest is up to date: NO — regenerate (" + why + ")")
            return 1
        out["generated"] = stamp
        expected = json.dumps(out, indent=2, ensure_ascii=False) + "\n"

        same = current == expected
        print("manifest generated " + stamp
              + "; freshness is enforced by validate-image-rights.js"
              + " --max-age-days")
        print("manifest is up to date: " + ("YES" if same else "NO — regenerate"))
        return 0 if same else 1

    MANIFEST.write_text(text, encoding="utf-8")
    print("VALIDATED %d record(s), %d live grant(s): %s"
          % (len(records), len(live), ", ".join(r["organisation_name"] for r in live)))
    print("wrote image-rights-manifest.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
