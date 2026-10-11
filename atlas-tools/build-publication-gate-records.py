#!/usr/bin/env python3
"""
BOUNDED BUILDER — THE PUBLICATION GATE FIELDS ON THE RIGHTS RECORDS
===================================================================
Adds `permission`, `listing_review`, `public_visibility` and `hold_reason` to
the BIOBUILDS row in image-rights-records.json and image-rights-manifest.json.

NO AIRTABLE WRITE. This records, in PlotNua's own files, a position that is
already true and already evidenced: BIOBUILDS granted permission on
2 October 2026 and asked to see the listing before it goes live.

WHY THE STRUCTURED FIELDS, when the prose note already says all this.

Because prose cannot be read by a gate. The note currently carries the whole
position in a paragraph, which means the only thing standing between a held
supplier and public Results is somebody reading carefully. The three states
below are the same facts in a shape a guard can assert.

AND BECAUSE THE DISTINCTION MATTERS. An earlier draft of PlotNua's own audit
described BIOBUILDS as a supplier whose publication "is not authorised". That
is not what happened. They said yes, with a condition. Collapsing "granted
with a review condition" into "not approved" misrepresents a supplier who
cooperated, and would have had PlotNua asking again for permission it already
held. `hold_reason` is therefore listing-review-awaiting-confirmation, never
no-permission, and PG5 asserts that it stays that way.

    python3 atlas-tools/build-publication-gate-records.py [--check] [--revert]

--check reports without writing. --revert restores the .bak sidecars.
Exit 0 = applied, or already correct.
"""
import argparse
import json
import pathlib
import shutil
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
TARGETS = [ROOT / "image-rights-records.json",
           ROOT / "image-rights-manifest.json"]

ORG = "ORG-000153"

# The three dimensions. Every value here is evidenced, not inferred.
PERMISSION = {
    "state": "GRANTED",
    "ref": "C2-GRANT-BIOBUILDS-20261002",
    "record": "rec6JPwNYPIj7EIfZ",
    "date": "2026-10-02",
    "scope": ["feature", "imagery"],
    "conditions": ["credit", "link-back", "pre-live-review",
                   "withdrawable-on-request"],
}
LISTING_REVIEW = {
    "state": "AWAITING_CONFIRMATION",
    "requested_by": "supplier",
    "requested_in": "C2-GRANT-BIOBUILDS-20261002",
    "corrections_received": "2026-10-11",
    "corrections_applied": ["edecc86", "7b81224"],
    "confirmed_at": None,
    "note": ("Mateus reviewed the original preview and asked for factual "
             "corrections on 11 October 2026. The corrections are applied and "
             "the revised preview awaits his confirmation. This is a granted "
             "permission's condition being exercised, not a permission "
             "withheld."),
}


def die(msg):
    print("REFUSED: " + msg)
    sys.exit(1)


def derive(permission, review, asset_state):
    """Mirror of derivePublicVisibility() in atlas-tools/publication-gate.mjs.

    Two implementations of one rule is exactly the duplication that creates a
    second answer, so the two are pinned together by G4 below: the guard runs
    the JS derivation over the written file and refuses if it disagrees."""
    perm, rev = permission.get("state"), review.get("state")
    if perm == "DECLINED":
        return "HOLD", "permission-declined"
    if perm == "NONE":
        return "HOLD", "no-permission"
    if perm == "CONDITIONAL":
        return "HOLD", "permission-conditional-unresolved"
    if perm != "GRANTED":
        return "HOLD", "permission-state-missing"
    if rev == "AWAITING_CONFIRMATION":
        return "HOLD", "listing-review-awaiting-confirmation"
    if rev == "CHANGES_REQUESTED":
        return "HOLD", "listing-review-changes-requested"
    if rev not in ("NOT_REQUIRED", "CONFIRMED"):
        return "HOLD", "listing-review-state-missing"
    if asset_state and asset_state != "APPROVED":
        return "HOLD", "assets-not-approved"
    return "PUBLISHABLE", None


def rows_of(doc):
    if isinstance(doc, list):
        return doc
    for v in doc.values():
        if isinstance(v, list) and v and isinstance(v[0], dict):
            return v
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--revert", action="store_true")
    args = ap.parse_args()

    # The eight exercised assets are still Reference Only in Atlas. That is a
    # real condition of the gate, not an assumption, and it is recorded so the
    # derivation can see it.
    asset_state = "REFERENCE_ONLY"
    visibility, hold_reason = derive(PERMISSION, LISTING_REVIEW, asset_state)

    # G1 · THE BUILDER REFUSES TO WRITE A PUBLISHABLE STATE.
    # This builder exists to record a hold. If the derivation ever came out
    # PUBLISHABLE here it would mean the inputs above had been edited, and
    # publishing a supplier must never be a side effect of running a recording
    # tool. Promotion is a separate, deliberate act.
    if visibility != "HOLD":
        die("the derivation produced %r, not HOLD. This builder records a "
            "hold and must never be the thing that publishes a supplier. "
            "Nothing written." % visibility)

    # G2 · THE REASON IS NEVER no-permission FOR A GRANTED SUPPLIER.
    if PERMISSION["state"] == "GRANTED" and hold_reason == "no-permission":
        die("hold_reason would say no-permission for a GRANTED supplier. "
            "Nothing written.")

    print("\nPUBLICATION GATE RECORDS")
    print("=" * 74)
    print("  derived   public_visibility = %s" % visibility)
    print("  derived   hold_reason       = %s" % hold_reason)
    print("  ok    G1  the builder cannot write a PUBLISHABLE state")
    print("  ok    G2  a GRANTED supplier is never called unpermitted")

    changed = []
    for path in TARGETS:
        if not path.exists():
            die("%s is missing." % path.name)
        bak = path.with_suffix(path.suffix + ".bak")

        if args.revert:
            if bak.exists():
                shutil.copyfile(bak, path)
                print("  reverted  %s" % path.name)
            continue

        doc = json.loads(path.read_text(encoding="utf-8"))
        rows = rows_of(doc)
        if rows is None:
            die("%s has no record list this builder recognises." % path.name)

        hits = [r for r in rows if r.get("organisation_code") == ORG]
        if len(hits) != 1:
            die("%s holds %d rows for %s, expected exactly 1. Nothing "
                "written." % (path.name, len(hits), ORG))
        row = hits[0]

        # G3 · THE EVIDENCE MUST STILL BE THERE. These fields describe a
        # grant; writing them onto a row that has lost its evidence would be
        # manufacturing a permission.
        if "happy for PlotNua to feature BioBuilds" not in str(row.get("evidence", "")):
            die("the BIOBUILDS grant evidence is not in %s. These fields "
                "describe that grant and must not be written without it." % path.name)

        before = json.dumps(row, sort_keys=True)
        row["permission"] = PERMISSION
        row["listing_review"] = LISTING_REVIEW
        row["asset_approval_state"] = asset_state
        row["public_visibility"] = visibility
        row["hold_reason"] = hold_reason
        after = json.dumps(row, sort_keys=True)

        if before == after:
            print("  ok        %s already carries the gate fields" % path.name)
            continue
        if args.check:
            print("  would     update %s" % path.name)
            continue
        if not bak.exists():
            shutil.copyfile(path, bak)
        path.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8")
        changed.append(path.name)
        print("  wrote     %s" % path.name)

    if args.revert:
        print("-" * 74)
        print("REVERTED.")
        return
    if args.check:
        print("-" * 74)
        print("CHECK ONLY. Nothing written.")
        return

    # G4 · ONE RULE, NOT TWO. The Python derivation above and the JS one in
    # publication-gate.mjs must agree on the file that was just written.
    # Without this, the duplication quietly becomes two different answers.
    probe = (
        "import {derivePublicVisibility} from '%s';"
        "import {readFileSync} from 'node:fs';"
        "const d=JSON.parse(readFileSync('%s','utf8'));"
        "const rows=Array.isArray(d)?d:Object.values(d).find(v=>Array.isArray(v)&&v[0]&&typeof v[0]==='object');"
        "const r=rows.find(x=>x.organisation_code==='%s');"
        "const o=derivePublicVisibility(r);"
        "console.log(JSON.stringify(o));"
        % ((HERE / "publication-gate.mjs").as_uri(), TARGETS[0], ORG))
    try:
        out = subprocess.run(["node", "--input-type=module", "-e", probe],
                             capture_output=True, text=True, timeout=60)
        if out.returncode != 0:
            die("the JS derivation could not be run to cross-check the "
                "Python one: %s" % (out.stderr or "").strip()[:200])
        js = json.loads(out.stdout.strip())
        if js.get("visibility") != visibility or js.get("holdReason") != hold_reason:
            die("the Python and JS derivations DISAGREE (%s/%s vs %s/%s). "
                "One rule, not two." % (visibility, hold_reason,
                                        js.get("visibility"), js.get("holdReason")))
        print("  ok    G4  the JS derivation agrees: %s / %s"
              % (js.get("visibility"), js.get("holdReason")))
    except (OSError, ValueError) as e:
        die("cross-check could not run: %s" % e)

    print("-" * 74)
    print("Recorded on %d file(s): %s" % (len(changed), ", ".join(changed) or "none"))
    print("No Airtable write. No public visibility change. BIOBUILDS stays "
          "on HOLD.")


if __name__ == "__main__":
    main()
