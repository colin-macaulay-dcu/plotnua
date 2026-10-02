#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BOUNDED BUILDER — the OGNYX image-rights record.

*** THIS IS A PREVIEW-SCOPED RECORD, NOT A PUBLICATION GRANT. ***

Fabian at OGNYX replied on 2 October 2026 asking to see the preview before
proceeding, and wrote, in his own words:

    "Please feel free to prepare the preview, including any example imagery,
     product presentation and links you propose to use."

That is written permission, and it is written permission for ONE THING: the
private preview. It is not approval to publish OGNYX imagery to homeowners,
and Atlas Permission Outcome stays "Unknown -- Awaiting Reply" until he says
so.

WHY A RECORD EXISTS AT ALL. The publish-time gate walks every .html in the
tree and refuses any externally-hosted image without a live grant. It has no
notion of a page, and noindex is not a rights state -- if it were, anyone
could publish anyone's photographs by adding a meta tag. Measured on
2 October 2026 before this file existed:

    REFUSE ognyx-preview.html -> .../Screenshot2025-08-13at21.01.07.png
           marked for publication but has NO organisation; rights cannot be
           established
    GATE FAILED -- 0 publishable, 1 refused

So the choice was a scoped record or no imagery. The gate was NOT weakened.
Instead this record is written as a conditional grant and then made NARROWER
than the gate would enforce, by atlas-tools/prove-preview-only-containment.mjs,
which refuses an OGNYX image on any page except ognyx-preview.html. That is
the BIOBUILDS pattern, and it is the founder's decision of 2 October 2026.

NO SHARED CDN HERE. OGNYX serve their images from www.ognyx.com itself, so
the scope is their own domain and no delivery-host prefix is needed. R3
refuses one anyway if somebody adds it later without thinking, because a
delivery host on a domain-scoped grant is a widening nobody asked for.

Run:  python3 .github/scripts/build-ognyx-grant.py [--check]
Then: python3 .github/scripts/generate_image_rights_manifest.py
"""

import json
import pathlib
import sys

CHECK = "--check" in sys.argv
ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
RECORDS = ROOT / "image-rights-records.json"

ORG = "recGxi1agXCBR1FLt"
CREDIT = "© OGNYX"
DOMAIN = "ognyx.com"
IPO_RECORD = "recIjRDMQ55nk6cOn"
IPO_REF = "WELLNESS-FIRST-OGNYX-20261002"
PREVIEW_PAGE = "ognyx-preview.html"


def die(why):
    print("REFUSED: " + why)
    sys.exit(1)


NEW = {
    "organisation_record": ORG,
    "organisation_name": "OGNYX",
    "permission_outcome": "Granted with Conditions — Founder Confirmed",
    "permitted_domain": DOMAIN,
    "required_credit": CREDIT,
    "evidence": (
        "Fabian of OGNYX replied on 2 October 2026 to the Home Wellness "
        "outreach, Gmail thread 1a0fd83e5f6c284f, message 1a0fe3d7b43366cf: "
        "“Before proceeding, we would be interested in seeing the preview of "
        "how OGNYX would be presented within PlotNua. Please feel free to "
        "prepare the preview, including any example imagery, product "
        "presentation and links you propose to use.” Recorded in Atlas as "
        "Image Permission Outreach " + IPO_REF + " (" + IPO_RECORD + ") "
        "against Organisations " + ORG + ", contact info@ognyx.com. THE "
        "OUTCOME IN ATLAS REMAINS “Unknown — Awaiting Reply”: he asked to "
        "see the preview, he did not say yes to publication."
    ),
    "conditions": [
        "PREVIEW ONLY. This permission covers " + PREVIEW_PAGE + " and "
        "nothing else. OGNYX imagery must not appear on any other page, in "
        "the public Results journey, or in any runtime Atlas payload, until "
        "OGNYX approve publication in writing.",
        "Credit '" + CREDIT + "' wherever the imagery appears.",
        "Link back to https://www.ognyx.com/ wherever the imagery appears.",
        "Images are used unmodified and served from OGNYX's own domain. "
        "Nothing is downloaded, re-hosted, cropped or altered.",
        "OGNYX may request change or removal of any image at any time, and "
        "PlotNua complies.",
        "No resale, no sublicensing, no unrelated advertising use. OGNYX "
        "retain ownership of the imagery.",
    ],
    "note": (
        "SCOPE: ognyx.com only. OGNYX serve their product images from their "
        "own domain, so there is no shared CDN to scope by prefix and no "
        "delivery host is declared.\n\n"
        "THIS ROW EXISTS TO LET THE PRIVATE PREVIEW PASS THE GATE, AND FOR "
        "NOTHING ELSE. The gate scopes a grant by host and has no notion of "
        "a page, so on its own this row would authorise OGNYX imagery "
        "anywhere in the tree. atlas-tools/prove-preview-only-containment.mjs "
        "is what keeps it to " + PREVIEW_PAGE + ", and that proof runs in CI "
        "beside the gate on every publish. If the preview is ever deleted, "
        "this record should go with it.\n\n"
        "FOUR ASSETS, all read first-party from ognyx.com on 2 October 2026 "
        "and all visually inspected before use: two photographs of the "
        "Stainless Steel Cold Plunge Tub for One, one visualisation of the "
        "1.6m Outdoor Sauna, and one visualisation of the Round Hot Tub with "
        "integrated wood-fired stove. The two visualisations are labelled as "
        "visualisations on the page, because showing a render as a "
        "photograph would misrepresent what a homeowner would receive."
    ),
    "atlas_permission_record": IPO_RECORD,
    "atlas_permission_ref": IPO_REF,
    "permission_date": "2026-10-02",
    "permitted_delivery_hosts": [],
}

doc = json.loads(RECORDS.read_text(encoding="utf-8"))
records = doc["records"]
before = json.dumps(records, sort_keys=True)

# ---- R0 . IDEMPOTENCE ------------------------------------------------------
if any(r.get("organisation_record") == ORG for r in records):
    die("OGNYX (" + ORG + ") already has a rights record. Nothing written.")

# ---- R1 . THE FILE IS THE ONE THIS WAS ANCHORED AGAINST -------------------
if len(records) != 11:
    die("expected 11 existing records, found %d. The file has moved since "
        "this builder was written; re-read it before trusting these guards."
        % len(records))

# ---- R2 . VOCABULARY ------------------------------------------------------
# The gate recognises a closed set. An invented outcome string -- "Granted --
# Preview Only" would read well here -- is refused by the gate as
# unrecognised, and an unrecognised outcome is not a grant. So the outcome is
# a real one and the SCOPE lives in the conditions, where the containment
# proof can read it.
LIVE = {
    "Granted — Founder Confirmed",
    "Granted — Supplier Confirmed (one-click)",
    "Granted with Conditions — Founder Confirmed",
}
if NEW["permission_outcome"] not in LIVE:
    die("permission outcome %r is not one the gate recognises."
        % NEW["permission_outcome"])

# ---- R3 . NO DELIVERY HOST ON A DOMAIN-SCOPED GRANT -----------------------
if NEW["permitted_delivery_hosts"]:
    die("a delivery host was declared. OGNYX serve from their own domain, so "
        "a delivery host is a widening of the scope that nobody asked for. "
        "If they move to a shared CDN, add the host WITH a path prefix and "
        "change this guard deliberately.")

# ---- R4 . DOMAIN ----------------------------------------------------------
if NEW["permitted_domain"] != DOMAIN:
    die("permitted_domain is %r, not the supplier's own domain %r."
        % (NEW["permitted_domain"], DOMAIN))

# ---- R5 . THE PREVIEW-ONLY CONDITION MUST SURVIVE -------------------------
# This is the whole reason the record is safe to exist. A copy of this record
# that lost it would be an ordinary publication grant for a supplier who has
# not granted publication.
conds = " ".join(NEW["conditions"]).lower()
if "preview only" not in conds:
    die("the PREVIEW ONLY condition is missing. Without it this record is an "
        "ordinary publication grant, and OGNYX have not granted publication.")
if PREVIEW_PAGE not in conds:
    die("the conditions do not name %s, so nothing states WHICH page the "
        "permission covers. The containment proof reads this." % PREVIEW_PAGE)
if "unknown — awaiting reply" not in NEW["evidence"].lower():
    die("the evidence does not record that Atlas still holds OGNYX at "
        "“Unknown — Awaiting Reply”. A record that reads as a yes, for a "
        "supplier who asked to see the preview first, is the exact mistake "
        "this field exists to prevent.")

# ---- R6 . PROVENANCE ------------------------------------------------------
for field in ("evidence", "atlas_permission_record", "atlas_permission_ref",
              "required_credit", "permission_date", "note"):
    if not NEW.get(field):
        die("the OGNYX record is missing %r. A permission that cannot be "
            "traced back to Atlas and to the supplier's own words is not a "
            "permission this repository will carry." % field)
if NEW["required_credit"] != CREDIT:
    die("the required credit is %r, not %r." % (NEW["required_credit"], CREDIT))

# ---- R7 . THE ELEVEN EXISTING RECORDS MUST BE UNTOUCHED -------------------
records.append(NEW)
if json.dumps(records[:11], sort_keys=True) != before:
    die("an existing rights record changed. This builder appends one record "
        "and alters nothing else.")
if len(records) != 12:
    die("expected 12 records after the append, found %d." % len(records))

if CHECK:
    print("CHECK ONLY — nothing written. 12 records would result.")
    sys.exit(0)

RECORDS.write_text(
    json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print("OGNYX PREVIEW-SCOPED RIGHTS RECORD")
print("=" * 74)
print("  ok    8 guards passed")
print("  ok    appended 1 record; 12 total")
print("  ok    scope: %s, no delivery host" % DOMAIN)
print("  ok    PREVIEW ONLY condition naming %s recorded" % PREVIEW_PAGE)
print("  ok    Atlas outcome stays 'Unknown — Awaiting Reply'")
print("-" * 74)
print("wrote " + str(RECORDS))
print("NEXT: python3 .github/scripts/generate_image_rights_manifest.py")
print("THEN: node atlas-tools/prove-preview-only-containment.mjs — this row "
      "is not safe without it.")
