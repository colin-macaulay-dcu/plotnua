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
    # The supplier's pre-live-review request is NOT removed and NOT satisfied.
    # It was asked for, it has not been answered, and the founder decided to
    # proceed anyway. All three facts are recorded; none is tidied away.
    "pre_live_review_disposition": {
        "requested_by_supplier": True,
        "answered_by_supplier": False,
        "proceeded_under": "FX-BIOBUILDS-PUBLISH-20261011",
        "note": ("BIOBUILDS asked to see the listing before it went live. The "
                 "corrections they requested on 11 October 2026 are "
                 "implemented. They have not confirmed the revised preview. "
                 "The founder decided to publish without that confirmation "
                 "and accepts responsibility for doing so. This supersedes "
                 "PlotNua's earlier reading that the grant covered the "
                 "private preview only -- that was PlotNua's own scoping of "
                 "its own restraint, not a limit BIOBUILDS placed on the "
                 "grant."),
    },
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

# ── THE FOUNDER'S DECISION, AS DATA ───────────────────────────────────────
#
# BIOBUILDS granted permission on 2 October 2026 to feature its products and
# to use selected imagery with credit and a link back. In the same message it
# asked to see the listing first. That check has not come back.
#
# The founder has decided to publish without it and to own that decision.
# This is the record of that, and it is deliberately NOT a change to the
# review state: Mateus has not confirmed, the record still says he has not
# confirmed, and `supplier_confirmation_received: False` says it a second time
# in the place a future reader is most likely to look.
FOUNDER_EXCEPTION = {
    "authorised_by": "Colin MacAulay",
    "role": "Founder",
    "decision_date": "2026-10-11",
    "decision_ref": "FX-BIOBUILDS-PUBLISH-20261011",
    "supplier_confirmation_received": False,
    "waives": [
        "listing-review-awaiting-confirmation",
        "assets-not-approved",
    ],
    "basis": (
        "BIOBUILDS granted written permission on 2 October 2026 to feature "
        "its products and to use selected imagery with credit and a link "
        "back (C2-GRANT-BIOBUILDS-20261002). The supplier then asked for "
        "factual corrections on 11 October 2026; those corrections are "
        "implemented in Atlas and in the private preview. The founder has "
        "decided to publish the corrected listing without waiting for the "
        "supplier's confirmation of the revised preview, and accepts "
        "responsibility for proceeding before that confirmation is received."
    ),
    "scope": (
        "Authorises PUBLICATION OF THE PRODUCT LISTING in public Results and "
        "Compare, AND publication of the SIX ENUMERATED ASSETS in "
        "approved_assets, each with the supplier's caption, the credit and a "
        "working link back. WIDENED 11 October 2026 by the same founder "
        "decision: the earlier version of this scope excluded imagery "
        "entirely, because at that point no imagery had been authorised. It "
        "does NOT authorise any asset outside that list -- every other "
        "BIOBUILDS asset, including the two exercised on the private "
        "preview, remains Reference Only, and "
        "prove-biobuilds-containment.mjs enforces the difference per asset "
        "rather than per domain."
    ),
    "withdrawal": (
        "BIOBUILDS may request change or removal at any time and PlotNua "
        "complies, exactly as the original grant provides. If the supplier "
        "objects to the published listing, remove this exception and the "
        "gate returns the product to HOLD with no other change."
    ),
}


# ── THE APPROVED ASSET SELECTION ─────────────────────────────────────────
#
# Founder authorisation, 11 October 2026, under
# FX-BIOBUILDS-PUBLISH-20261011: selected BIOBUILDS imagery may be published,
# within the scope of the written grant of 2 October 2026.
#
# APPROVAL IS BY ENUMERATION. An asset is publishable because it is in this
# list, never because it is on the supplier's domain. The two assets exercised
# on the preview that are NOT here -- wall-section-3.0 and
# prefab-48-crane-lift -- remain REFERENCE_ONLY, as do the other 26 governed
# assets.
#
# NO ALT TEXT HERE SAYS photograph, photo, render OR visualisation. Grant
# condition 7 records that BIOBUILDS has never said which the model imagery
# is, and that until they answer no PlotNua surface may describe it as either.
# The supplier's own caption is medium-neutral and is used verbatim.
MEDIA_PREFIX = "https://www.biobuilds.com/_next/static/immutable/media/"
SUPPLIER_CAPTION = "BIOBUILDS model imagery"
SUPPLIER_CREDIT = "\u00a9 BIOBUILDS"
SUPPLIER_LINK = "https://www.biobuilds.com/"

APPROVED_ASSETS = [
    {
        "url": MEDIA_PREFIX + "wanderlust-catalog.3-furbv0o-vtc.jpg",
        "product_code": "PROD-000523",
        "product_name": "BIOBUILDS Wanderlust",
        "role": "exterior",
        "primary": True,
        "alt": "The BIOBUILDS Wanderlust 48 seen from outside, a timber-clad "
               "single-storey building with full-height glazing.",
    },
    {
        "url": MEDIA_PREFIX + "wanderlust-48-int-catalog.0d9n8s-fzmg7q.jpg",
        "product_code": "PROD-000523",
        "product_name": "BIOBUILDS Wanderlust",
        "role": "interior",
        "primary": False,
        "alt": "Inside the BIOBUILDS Wanderlust 48, an open living space with "
               "timber finishes and glazing to the garden.",
    },
    {
        "url": MEDIA_PREFIX + "wanderlust-48-bedroom.02gun-re0wb_5.jpg",
        "product_code": "PROD-000523",
        "product_name": "BIOBUILDS Wanderlust",
        "role": "interior",
        "primary": False,
        "alt": "A bedroom in the BIOBUILDS Wanderlust 48, with timber walls "
               "and a window to the garden.",
    },
    {
        "url": MEDIA_PREFIX + "serenity-catalog.2xcd8x45pacpa.jpg",
        "product_code": "PROD-000524",
        "product_name": "BIOBUILDS Serenity",
        "role": "exterior",
        "primary": True,
        "alt": "The BIOBUILDS Serenity 95 seen from outside, a larger "
               "timber-clad house with extensive glazing.",
    },
    {
        "url": MEDIA_PREFIX + "serenity-95-int-catalog.0uuneoqa7y-h8.jpg",
        "product_code": "PROD-000524",
        "product_name": "BIOBUILDS Serenity",
        "role": "interior",
        "primary": False,
        "alt": "Inside the BIOBUILDS Serenity 95, an open-plan living and "
               "dining space with timber finishes.",
    },
    {
        "url": MEDIA_PREFIX + "serenity-95-bathroom.1nmu58m7tl0_u.jpg",
        "product_code": "PROD-000524",
        "product_name": "BIOBUILDS Serenity",
        "role": "interior",
        "primary": False,
        "alt": "A bathroom in the BIOBUILDS Serenity 95, with tiled surfaces "
               "and fixed sanitaryware.",
    },
]

# Exercised on the private preview and DELIBERATELY NOT approved: neither
# depicts a product a homeowner is choosing between.
WITHHELD_ASSETS = [
    {"url": MEDIA_PREFIX + "wall-section-3.0.26fqr4wmqyq13.jpg",
     "reason": "a construction detail of the wall build-up, not a product"},
    {"url": MEDIA_PREFIX + "prefab-48-crane-lift.2fhf6txqe9e82.jpg",
     "reason": "a process shot of a module being craned, not a product"},
]

ASSET_APPROVAL = {
    "state": "SELECTED_ASSETS_APPROVED",
    "default_for_unlisted": "REFERENCE_ONLY",
    "approved_count": len(APPROVED_ASSETS),
    "withheld_on_preview": len(WITHHELD_ASSETS),
    "governed_total_in_atlas": 34,
    "authorised_by": "FX-BIOBUILDS-PUBLISH-20261011",
    "note": ("Approval is by ENUMERATION, per asset. An asset is publishable "
             "because it appears in approved_assets, never because it is "
             "served from the supplier's domain. Every asset not listed "
             "remains Reference Only - Not Published, including the two "
             "exercised on the private preview. The internal REFERENCE_ONLY "
             "state was never a refusal by BIOBUILDS; it was PlotNua's own "
             "publication restriction, and the founder has lifted it for the "
             "six selected assets only."),
    "conditions_on_every_use": [
        "Caption: " + SUPPLIER_CAPTION,
        "Credit: " + SUPPLIER_CREDIT,
        "A working link to " + SUPPLIER_LINK,
        "No PlotNua surface describes the medium: grant condition 7 stands "
        "until BIOBUILDS answers.",
        "No surface implies the imagery shows a completed installation in "
        "Ireland.",
    ],
}


# REVOKED 16 October 2026 -- founder instruction, Atlas Population Phase 2:
# "BIOBUILDS: correct the five products incorrectly marked PUBLISHABLE and
# preserve the supplier's explicit pre-publication review requirement."
# FOUNDER_EXCEPTION above is kept verbatim as the historical record of what was
# decided on 11 October. It is no longer ACTIVE: the derivation receives no
# exception, so the outstanding listing review holds BIOBUILDS again, exactly
# as the exception's own 'withdrawal' clause describes ("remove this exception
# and the gate returns the product to HOLD with no other change"). Nothing about
# the grant, the review state, the evidence or the imagery permission changes.
ACTIVE_FOUNDER_EXCEPTION = None
FOUNDER_EXCEPTION_REVOCATION = {
    "revokes": "FX-BIOBUILDS-PUBLISH-20261011",
    "revoked_on": "2026-10-16",
    "authorised_by": "Colin MacAulay",
    "role": "Founder",
    "decision": ("Atlas Population Phase 2, 16 October 2026: correct the five "
                 "BIOBUILDS products marked PUBLISHABLE and preserve the "
                 "supplier's explicit pre-publication review requirement."),
    "effect": ("public_visibility returns to HOLD with hold_reason "
               "listing-review-awaiting-confirmation. Permission, listing "
               "review state, evidence, conditions and asset enumeration are "
               "unchanged. BIOBUILDS returns to PUBLISHABLE only when the "
               "supplier confirms the corrected listing (listing_review.state "
               "CONFIRMED) -- never by re-adding an exception without a new "
               "founder decision."),
    "supplier_confirmation_received": False,
}


def die(msg):
    print("REFUSED: " + msg)
    sys.exit(1)


# The four reasons no decision can waive. Kept in step with NEVER_WAIVABLE in
# atlas-tools/publication-gate.mjs, and G5 below refuses to run if the two
# lists ever diverge -- a mirror that drifts is worse than no mirror.
NEVER_WAIVABLE = (
    "permission-declined",
    "no-permission",
    "permission-conditional-unresolved",
    "permission-state-missing",
)


def derive(permission, review, asset_state, exception=None):
    """Mirror of derivePublicVisibility() in atlas-tools/publication-gate.mjs.

    Returns (visibility, hold_reason, waived).

    Two implementations of one rule is exactly the duplication that creates a
    second answer, so the two are pinned together by G4 below: the guard runs
    the JS derivation over the written file and refuses if it disagrees."""
    perm, rev = permission.get("state"), review.get("state")
    conditions = [
        (perm not in ("GRANTED", "CONDITIONAL", "DECLINED", "NONE"),
         "permission-state-missing"),
        (rev not in ("NOT_REQUIRED", "AWAITING_CONFIRMATION", "CONFIRMED",
                     "CHANGES_REQUESTED"), "listing-review-state-missing"),
        (perm == "DECLINED", "permission-declined"),
        (perm == "NONE", "no-permission"),
        (perm == "CONDITIONAL", "permission-conditional-unresolved"),
        (rev == "AWAITING_CONFIRMATION", "listing-review-awaiting-confirmation"),
        (rev == "CHANGES_REQUESTED", "listing-review-changes-requested"),
        (bool(asset_state) and asset_state != "APPROVED", "assets-not-approved"),
    ]
    accepted = list((exception or {}).get("waives") or ())
    waived = []
    for unsatisfied, reason in conditions:
        if not unsatisfied:
            continue
        if reason in accepted and reason not in NEVER_WAIVABLE:
            waived.append(reason)
            continue
        return "HOLD", reason, waived
    return "PUBLISHABLE", None, waived


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
    visibility, hold_reason, waived = derive(
        PERMISSION, LISTING_REVIEW, asset_state, ACTIVE_FOUNDER_EXCEPTION)

    # G1 · A PUBLISHABLE STATE MUST BE FULLY ACCOUNTED FOR.
    #
    # This guard used to refuse PUBLISHABLE outright, because until 11 October
    # 2026 this builder only ever recorded a hold and publishing a supplier
    # must never be a side effect of running a recording tool.
    #
    # It is now the writer of a founder-authorised publication, so an outright
    # refusal would be wrong. What it refuses instead is an UNEXPLAINED
    # publication: PUBLISHABLE is permitted only when every condition that
    # would otherwise have held the supplier was explicitly named in the
    # founder's decision. A supplier cannot become publishable here because an
    # input was quietly edited -- only because a decision says so, in writing,
    # naming what it accepts.
    if visibility == "PUBLISHABLE":
        if not waived:
            die("the derivation produced PUBLISHABLE with nothing waived, "
                "which means the recorded inputs no longer describe a held "
                "supplier. Publishing must not be a side effect of running "
                "this tool. Nothing written.")
        unexplained = [w for w in waived
                       if w not in ((ACTIVE_FOUNDER_EXCEPTION or {}).get("waives") or ())]
        if unexplained:
            die("these conditions were waived without being named in the "
                "founder's decision: %s. Nothing written." % unexplained)
        for w in waived:
            if w in NEVER_WAIVABLE:
                die("the derivation waived %r, which no decision may waive. "
                    "Nothing written." % w)

    # G1b · AND THE DECISION MUST NOT CLAIM A CONFIRMATION.
    # The one thing the founder explicitly forbade: do not record Mateus as
    # having confirmed the corrected preview.
    if (ACTIVE_FOUNDER_EXCEPTION is not None and
            ACTIVE_FOUNDER_EXCEPTION.get("supplier_confirmation_received") is not False):
        die("the founder exception does not state that the supplier's "
            "confirmation is OUTSTANDING. An exception records proceeding "
            "WITHOUT confirmation. Nothing written.")
    if LISTING_REVIEW.get("state") == "CONFIRMED" or LISTING_REVIEW.get("confirmed_at"):
        die("the listing review would record a confirmation the supplier has "
            "not given. Nothing written.")

    # G2 · THE REASON IS NEVER no-permission FOR A GRANTED SUPPLIER.
    if PERMISSION["state"] == "GRANTED" and hold_reason == "no-permission":
        die("hold_reason would say no-permission for a GRANTED supplier. "
            "Nothing written.")

    print("\nPUBLICATION GATE RECORDS")
    print("=" * 74)
    print("  derived   public_visibility = %s" % visibility)
    print("  derived   hold_reason       = %s" % hold_reason)
    if visibility == "PUBLISHABLE":
        print("  ok    G1  the publication is fully accounted for by the "
              "founder decision")
        print("            waived: %s" % ", ".join(waived))
    else:
        print("  ok    G1  the builder cannot write an unexplained "
              "PUBLISHABLE state")
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
        row["asset_approval"] = ASSET_APPROVAL
        row["approved_assets"] = APPROVED_ASSETS
        row["withheld_assets"] = WITHHELD_ASSETS
        if ACTIVE_FOUNDER_EXCEPTION is not None:
            row["founder_exception"] = ACTIVE_FOUNDER_EXCEPTION
            row.pop("founder_exception_revoked", None)
        else:
            row.pop("founder_exception", None)
            row["founder_exception_revoked"] = dict(
                FOUNDER_EXCEPTION_REVOCATION, original=FOUNDER_EXCEPTION)
        row["public_visibility"] = visibility
        row["hold_reason"] = hold_reason
        # The conditions that were unsatisfied and accepted. Written down so a
        # reader of this file never has to infer WHY a supplier with an
        # outstanding review is publishable, and so no surface can mistake a
        # waived condition for a satisfied one.
        row["waived_conditions"] = waived
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
        if sorted(js.get("waived") or []) != sorted(waived):
            die("the two derivations disagree about what was WAIVED (%s vs "
                "%s). One rule, not two." % (waived, js.get("waived")))
        print("  ok    G4  the JS derivation agrees: %s / %s / waived %s"
              % (js.get("visibility"), js.get("holdReason"),
                 js.get("waived")))

        # G5 · THE TWO FORBIDDEN LISTS MUST NOT DRIFT. The Python mirror above
        # carries its own copy of NEVER_WAIVABLE; if the JS one ever gained a
        # reason this did not, a decision could waive it here and be refused
        # there, or worse, the other way round.
        probe2 = ("import {NEVER_WAIVABLE} from '%s';"
                  "console.log(JSON.stringify(NEVER_WAIVABLE));"
                  % (HERE / "publication-gate.mjs").as_uri())
        out2 = subprocess.run(["node", "--input-type=module", "-e", probe2],
                              capture_output=True, text=True, timeout=60)
        if out2.returncode != 0:
            die("NEVER_WAIVABLE could not be read from the JS gate: %s"
                % (out2.stderr or "").strip()[:200])
        if sorted(json.loads(out2.stdout.strip())) != sorted(NEVER_WAIVABLE):
            die("the Python and JS NEVER_WAIVABLE lists have drifted apart. "
                "Nothing written.")
        print("  ok    G5  both NEVER_WAIVABLE lists agree (%d reasons)"
              % len(NEVER_WAIVABLE))
    except (OSError, ValueError) as e:
        die("cross-check could not run: %s" % e)

    print("-" * 74)
    print("Recorded on %d file(s): %s" % (len(changed), ", ".join(changed) or "none"))
    print("No Airtable write.")
    if ACTIVE_FOUNDER_EXCEPTION is not None:
        print("BIOBUILDS is PUBLISHABLE on a founder-authorised exception "
              "(%s, %s)." % (ACTIVE_FOUNDER_EXCEPTION["decision_ref"],
                             ACTIVE_FOUNDER_EXCEPTION["decision_date"]))
    else:
        print("BIOBUILDS is %s (%s): exception %s revoked %s."
              % (visibility, hold_reason,
                 FOUNDER_EXCEPTION_REVOCATION["revokes"],
                 FOUNDER_EXCEPTION_REVOCATION["revoked_on"]))
    print("The supplier's confirmation of the corrected preview remains "
          "OUTSTANDING and the record says so.")
    print("Imagery: %d asset(s) approved for publication, %d withheld on "
          "the preview," % (len(APPROVED_ASSETS), len(WITHHELD_ASSETS)))
    print("and every other governed BIOBUILDS asset remains Reference Only.")
    print("Grant condition 7 stands: no surface describes the medium.")


if __name__ == "__main__":
    main()
