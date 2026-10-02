#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BOUNDED BUILDER — the BIOBUILDS rights record, for the private review preview
ONLY.

WHAT THIS IS FOR, AND WHAT IT IS CAREFUL NOT TO BE.

BIOBUILDS granted on 2 October 2026 with one condition attached: send the
listing for review before it goes live. The grant therefore supports exactly
one thing today -- showing BIOBUILDS their own listing on the private preview
URL they were already given three times -- and does not support public
publication.

Those are two different mechanisms in this repository, and they are not
connected:

  (1) GOING LIVE IN RESULTS is decided by pnResultPublishable -> the runtime
      product payload's image block, which is written ONLY for Atlas assets
      whose Publication Status is Approved. All 34 governed BIOBUILDS assets
      are 'Reference Only -- Not Published'. This record does not touch Atlas
      and cannot promote them. prove-results-publication-gate.mjs does not
      read the manifest at all.

  (2) PUBLISH-TIME CI is decided by validate-image-rights.js --scan-html
      against image-rights-manifest.json. A deployed page carrying a
      biobuilds.com image fails CI unless a live grant covers it. That is the
      one thing this record provides.

So this record is what lets the ALREADY-PROMISED private preview carry the
supplier's own imagery. It is not, and must not become, permission to publish.
The containment guard, prove-biobuilds-containment.mjs, is the other half: it
refuses the build if a biobuilds.com image ever appears on any page other than
the noindexed preview, or if that page loses its robots directives. Without it
this record would be wider than the grant, because the manifest scopes by host
and prefix and has no notion of a page.

NO DELIVERY HOST IS DECLARED. BIOBUILDS serve their own images from
www.biobuilds.com/_next/static/immutable/media/, so the first-party domain is
the whole scope, and the gate already treats www as the same host. Declaring a
CDN here would widen the grant to somebody else's files.

Run:  python3 .github/scripts/build-biobuilds-review-grant.py [--check]
Then: python3 .github/scripts/generate_image_rights_manifest.py
"""

import json
import pathlib
import sys

CHECK = "--check" in sys.argv
ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
RECORDS = ROOT / "image-rights-records.json"

ORG = "recjNpnrIr2KT5BWh"
CREDIT = "© BIOBUILDS"
DOMAIN = "biobuilds.com"
IPO_RECORD = "rec6JPwNYPIj7EIfZ"
IPO_REF = "C2-GRANT-BIOBUILDS-20261002"


def die(why):
    print("REFUSED: " + why)
    sys.exit(1)


NEW = {
    "organisation_record": ORG,
    "organisation_code": "ORG-000153",
    "organisation_name": "BIOBUILDS",
    "permission_outcome": "Granted with Conditions — Founder Confirmed",
    "permitted_domain": DOMAIN,
    "required_credit": CREDIT,
    "evidence": (
        "Mateus, BIOBUILDS, to PlotNua from marketing@biobuilds.com, Gmail "
        "thread 1a0d05d7cd1d4aea, message 1a0fc4a334452803, 2026-10-02 "
        "11:05:03 UTC: \"Yes. We are happy for PlotNua to feature BioBuilds "
        "and use selected images from our website, with credit and a link "
        "back to us. We supply the Republic of Ireland. Please send us the "
        "listing before it goes live, so we can check it.\" Recorded in Atlas "
        "as Image Permission Outreach " + IPO_REF + " (" + IPO_RECORD + ") "
        "against Organisations ORG-000153 (" + ORG + "), outcome 'Granted "
        "with Conditions — Founder Confirmed'."
    ),
    "conditions": [
        "Credit '" + CREDIT + "' on every image use.",
        "Link back to https://www.biobuilds.com/ wherever the imagery appears.",
        "PRE-LIVE REVIEW: BIOBUILDS asked for the listing before it goes live. "
        "This grant therefore covers the private, noindexed review preview "
        "ONLY. Public publication waits for BIOBUILDS to come back.",
        "BIOBUILDS may request change or removal of any image at any time, "
        "and PlotNua complies.",
        "No resale, no sublicensing, no unrelated advertising use.",
        "BIOBUILDS retains ownership of the imagery.",
        "THE MEDIUM OF THE MODEL IMAGERY IS NOT ESTABLISHED. BIOBUILDS has "
        "not said whether the model images on their site are photographs of "
        "completed homes or architectural visualisations, and the question "
        "has been put to them. Until they answer, no PlotNua surface may "
        "describe them as either.",
    ],
    "note": (
        "SCOPE IS THE PRIVATE REVIEW PREVIEW, NOT PUBLICATION. Exercised on "
        "one page only, biobuilds-preview.html, which carries 'noindex, "
        "nofollow, noarchive, nosnippet, noimageindex', appears in no "
        "sitemap, and is reachable only by the URL BIOBUILDS were already "
        "sent on 23 September, 24 September and 2 October 2026. "
        "atlas-tools/prove-biobuilds-containment.mjs enforces exactly that "
        "and fails CI if a biobuilds.com image appears anywhere else or if "
        "that page loses a robots directive.\n\n"
        "ALL 34 GOVERNED BIOBUILDS ASSETS REMAIN 'Reference Only — Not "
        "Published' IN ATLAS, verified 2 October 2026. Results publishability "
        "is decided by the runtime product payload's image block, which is "
        "written only for Approved assets, so BIOBUILDS cannot reach the "
        "Results pool while that is true. This manifest row does not and "
        "cannot change it.\n\n"
        "Eight of the 34 are exercised on the preview: Wanderlust 48 "
        "(wanderlust-catalog, int-catalog, bedroom), Serenity 95 "
        "(serenity-catalog, int-catalog, bathroom), Construction "
        "(wall-section-3.0) and Process (prefab-48-crane-lift). All are "
        "served unmodified from BIOBUILDS' own origin and never rehosted. "
        "Sanctuary 142, Bloom 190 and Nest 24 are governed in Atlas but no "
        "product records exist for them and none were created to support the "
        "preview.\n\n"
        "WHEN BIOBUILDS REPLIES: if they approve, publication is a separate "
        "decision that needs the Atlas assets promoted to Approved and the "
        "containment guard revisited. If they decline or go quiet, this row "
        "is the thing to withdraw -- add withdrawal_effective_at and "
        "regenerate, and the gate will refuse the imagery on the next build."
    ),
    "atlas_permission_record": IPO_RECORD,
    "atlas_permission_ref": IPO_REF,
    "permission_date": "2026-10-02",
}

doc = json.loads(RECORDS.read_text(encoding="utf-8"))
records = doc["records"]
before = json.dumps(records, sort_keys=True)

# ---- R0 . IDEMPOTENCE. ------------------------------------------------------
# A second run must refuse rather than append a duplicate grant.
if any(r.get("organisation_record") == ORG for r in records):
    die("BIOBUILDS (" + ORG + ") already has a rights record. Nothing written.")

# ---- R1 . THE FILE IS THE ONE THIS WAS ANCHORED AGAINST. --------------------
if len(records) != 9:
    die("expected 9 existing records, found %d. The file has moved since this "
        "builder was written; re-read it before trusting these guards."
        % len(records))

# ---- R2 . VOCABULARY. The gate spells outcomes exactly; an outcome it would --
# not recognise must be refused HERE, not in CI with a worse message.
LIVE = {
    "Granted — Founder Confirmed",
    "Granted — Supplier Confirmed (one-click)",
    "Granted with Conditions — Founder Confirmed",
}
if NEW["permission_outcome"] not in LIVE:
    die("permission outcome %r is not one the gate recognises."
        % NEW["permission_outcome"])

# ---- R3 . NO DELIVERY HOST. BIOBUILDS serve their own images; a CDN entry ---
# here would reach files that are not theirs.
if "permitted_delivery_hosts" in NEW:
    die("a delivery host was declared for BIOBUILDS. They serve their own "
        "imagery from their own domain, so any CDN entry here would widen the "
        "grant beyond what was given.")

# ---- R4 . THE DOMAIN IS THEIRS AND NOTHING ELSE. ---------------------------
if NEW["permitted_domain"] != DOMAIN:
    die("permitted_domain is %r, not the supplier's own domain %r."
        % (NEW["permitted_domain"], DOMAIN))
# Read ONLY the host-bearing fields, never the prose: a guard that scans the
# whole record will one day refuse its own correct build because the evidence
# quotes a social URL.
hosts = [NEW.get("permitted_domain", "")] + [
    h.get("host", "") for h in NEW.get("permitted_delivery_hosts", [])]
for bad in ("instagram", "facebook", "linkedin", "cdninstagram", "fbcdn"):
    if any(bad in h.lower() for h in hosts):
        die("a social or third-party host (%r) appears among the BIOBUILDS "
            "permitted hosts. The grant reaches imagery on their website "
            "only." % bad)

# ---- R5 . THE CONDITIONS MUST CARRY THE TWO FACTS THAT CONSTRAIN USE. -------
# The pre-live review is the condition the supplier actually stated, and the
# unestablished medium is the thing most likely to be lost. If either sentence
# is gone, the record no longer records the grant that was given.
conds = " ".join(NEW["conditions"]).lower()
if "pre-live review" not in conds or "before it goes live" not in conds:
    die("the pre-live review condition is missing from the BIOBUILDS record. "
        "That condition is the grant; without it this row would read as "
        "permission to publish.")
if "medium" not in conds or "not established" not in conds:
    die("the unestablished-medium condition is missing. BIOBUILDS has not "
        "said what the model imagery is, and a record that forgets that will "
        "let a later surface assert it.")

# ---- R6 . PROVENANCE. A live grant with no traceable evidence is not one. ---
for field in ("evidence", "atlas_permission_record", "atlas_permission_ref",
              "required_credit", "permission_date", "note"):
    if not NEW.get(field):
        die("the BIOBUILDS record is missing %r. A grant that cannot be "
            "traced back to Atlas and to the supplier's own words is not a "
            "grant this repository will carry." % field)
if NEW["required_credit"] != CREDIT:
    die("the required credit is %r, not the exact wording the supplier asked "
        "for, %r." % (NEW["required_credit"], CREDIT))

# ---- R7 . THE NOTE MUST STATE THE REFERENCE-ONLY ATLAS STATE. --------------
# This is the sentence that stops a future reader mistaking this row for
# publication clearance.
if "Reference Only" not in NEW["note"]:
    die("the note does not record that the governed Atlas assets remain "
        "Reference Only. Without that sentence this row looks like clearance "
        "to publish.")

# ---- R8 . THE NINE EXISTING RECORDS MUST BE UNTOUCHED. ---------------------
records.append(NEW)
if json.dumps(records[:9], sort_keys=True) != before:
    die("an existing rights record changed. This builder appends one record "
        "and alters nothing else.")
if len(records) != 10:
    die("expected 10 records after the append, found %d." % len(records))

if CHECK:
    print("CHECK ONLY — nothing written. 10 records would result.")
    sys.exit(0)

RECORDS.write_text(
    json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print("BIOBUILDS RIGHTS RECORD")
print("=" * 74)
print("  ok    8 guards passed")
print("  ok    appended 1 record; 10 total")
print("  ok    scope: biobuilds.com, no delivery host, credit '%s'" % CREDIT)
print("  ok    pre-live review and unestablished-medium conditions recorded")
print("-" * 74)
print("wrote " + str(RECORDS))
print("NEXT: python3 .github/scripts/generate_image_rights_manifest.py")
