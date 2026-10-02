#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BOUNDED BUILDER — the Tanktribe image-rights record.

Tanktribe replied YES on 2 October 2026 to the Home Wellness outreach:
explicit permission to feature Tanktribe and use selected website imagery
with clear credit and a link back. Atlas holds that as Permission Outcome
"Granted -- Founder Confirmed" on WELLNESS-FIRST-TANKTRIBE-20261002, and all
six governed assets are Publication Status "Approved".

So unlike Cosy Cabins and Irish Sauna Company, this supplier HAS granted, and
the preview can carry their photographs. This record is what lets the
publish-time gate pass them.

THE DELIVERY-HOST SCOPE IS THE POINT. Tanktribe's site is Squarespace, so
their photographs are served from images.squarespace-cdn.com -- a host shared
with every other Squarespace site on the internet. The grant is scoped to
their own site namespace, /content/v1/67ac8d737a7c665f57f5babe/, and a bare
CDN host would authorise strangers' imagery. The generator refuses a delivery
host without a prefix; this builder refuses a wrong or widened one.

Run:  python3 .github/scripts/build-tanktribe-grant.py [--check]
Then: python3 .github/scripts/generate_image_rights_manifest.py
"""

import json
import pathlib
import sys

CHECK = "--check" in sys.argv
ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
RECORDS = ROOT / "image-rights-records.json"

ORG = "reclPfKiOQHdGJNGK"
CREDIT = "© Tanktribe"
DOMAIN = "tanktribe.ie"
CDN_HOST = "images.squarespace-cdn.com"
CDN_PREFIX = "/content/v1/67ac8d737a7c665f57f5babe/"
IPO_RECORD = "recHf6UOaAVMmmoGA"
IPO_REF = "WELLNESS-FIRST-TANKTRIBE-20261002"


def die(why):
    print("REFUSED: " + why)
    sys.exit(1)


NEW = {
    "organisation_record": ORG,
    "organisation_name": "Tanktribe",
    "permission_outcome": "Granted — Founder Confirmed",
    "permitted_domain": DOMAIN,
    "required_credit": CREDIT,
    "evidence": (
        "Tanktribe replied “YES” on 2 October 2026 to the Home "
        "Wellness outreach, Gmail thread 1a0fd832b4b384f2, giving explicit "
        "permission to feature Tanktribe and use selected website imagery "
        "with clear credit and a link back. Recorded in Atlas as Image "
        "Permission Outreach " + IPO_REF + " (" + IPO_RECORD + ") against "
        "Organisations " + ORG + ", outcome “Granted — Founder "
        "Confirmed”, contact info@tanktribe.ie."
    ),
    "conditions": [
        "Credit '" + CREDIT + "' wherever the imagery appears.",
        "Link back to https://www.tanktribe.ie/ wherever the imagery appears.",
        "Tanktribe may request change or removal of any image at any time, "
        "and PlotNua complies.",
        "No resale, no sublicensing, no unrelated advertising use.",
        "Tanktribe retains ownership of the imagery.",
        "AI-LABELLED ASSETS ARE EXCLUDED. Files published under 'ChatGPT "
        "Image ...' names on tanktribe.ie are not governed and must not be "
        "used: the grant covers the supplier's photography, and an "
        "AI-generated asset shown as a product photograph would misrepresent "
        "what a homeowner would receive.",
    ],
    "note": (
        "SCOPE: tanktribe.ie plus the supplier's own Squarespace namespace on "
        "the shared CDN. The bare host would authorise every Squarespace site "
        "in the world, so the prefix " + CDN_PREFIX + " is load-bearing.\n\n"
        "SIX GOVERNED ASSETS, all Publication Status 'Approved' and Rights "
        "Status 'Supplier Provided' in Atlas as at 2 October 2026 — three "
        "WILD TUB (IMG_2518, IMG_2580+3, IMG_2531) and three CORE (IMG_8495, "
        "IMG_8455, DSC_2111). Every one is a photograph. The AI-labelled "
        "files on the same site were deliberately excluded from ingestion and "
        "the exclusion is recorded as a condition above so it survives this "
        "record.\n\n"
        "Exercised on tanktribe-preview.html, which carries the credit and "
        "the link back. The gate refuses these images if the credit ever "
        "disappears from the page."
    ),
    "atlas_permission_record": IPO_RECORD,
    "atlas_permission_ref": IPO_REF,
    "permission_date": "2026-10-02",
    "permitted_delivery_hosts": [
        {
            "host": CDN_HOST,
            "path_prefix": CDN_PREFIX,
            "why": "Tanktribe's own Squarespace site namespace; the "
                   "identifier is their site id, so the scope is their files "
                   "and nobody else's."
        }
    ],
}

doc = json.loads(RECORDS.read_text(encoding="utf-8"))
records = doc["records"]
before = json.dumps(records, sort_keys=True)

# ---- R0 . IDEMPOTENCE ------------------------------------------------------
if any(r.get("organisation_record") == ORG for r in records):
    die("Tanktribe (" + ORG + ") already has a rights record. Nothing written.")

# ---- R1 . THE FILE IS THE ONE THIS WAS ANCHORED AGAINST -------------------
if len(records) != 10:
    die("expected 10 existing records, found %d. The file has moved since "
        "this builder was written; re-read it before trusting these guards."
        % len(records))

# ---- R2 . VOCABULARY ------------------------------------------------------
LIVE = {
    "Granted — Founder Confirmed",
    "Granted — Supplier Confirmed (one-click)",
    "Granted with Conditions — Founder Confirmed",
}
if NEW["permission_outcome"] not in LIVE:
    die("permission outcome %r is not one the gate recognises."
        % NEW["permission_outcome"])

# ---- R3a . THE BARE CDN ---------------------------------------------------
# Checked before the shape check, so this narrow failure cannot be masked.
for h in NEW["permitted_delivery_hosts"]:
    if not h.get("path_prefix"):
        die("a delivery host was declared without a path prefix. "
            + CDN_HOST + " is shared with every Squarespace site on the "
            "internet; a bare host would authorise all of them.")
    if h["host"] == CDN_HOST and h["path_prefix"] != CDN_PREFIX:
        die("the Squarespace prefix is %r, not Tanktribe's own namespace %r. "
            "A neighbouring prefix is somebody else's photography."
            % (h["path_prefix"], CDN_PREFIX))

# ---- R3b . SHAPE ----------------------------------------------------------
if len(NEW["permitted_delivery_hosts"]) != 1:
    die("expected exactly one delivery host, found %d. The grant covers "
        "their own site and its CDN namespace, nothing further."
        % len(NEW["permitted_delivery_hosts"]))

# ---- R4 . DOMAIN ----------------------------------------------------------
if NEW["permitted_domain"] != DOMAIN:
    die("permitted_domain is %r, not the supplier's own domain %r."
        % (NEW["permitted_domain"], DOMAIN))

# ---- R5 . THE AI-EXCLUSION CONDITION MUST SURVIVE -------------------------
# This is the condition most likely to be lost, because it is the one that
# constrains PlotNua rather than the supplier.
conds = " ".join(NEW["conditions"]).lower()
if "chatgpt image" not in conds or "ai-labelled" not in conds:
    die("the AI-labelled-asset exclusion is missing from the conditions. "
        "Tanktribe's site carries 'ChatGPT Image ...' files, and a grant "
        "record that forgets to exclude them will let one be shown to a "
        "homeowner as a product photograph.")

# ---- R6 . PROVENANCE ------------------------------------------------------
for field in ("evidence", "atlas_permission_record", "atlas_permission_ref",
              "required_credit", "permission_date", "note"):
    if not NEW.get(field):
        die("the Tanktribe record is missing %r. A grant that cannot be "
            "traced back to Atlas and to the supplier's own words is not a "
            "grant this repository will carry." % field)
if NEW["required_credit"] != CREDIT:
    die("the required credit is %r, not %r." % (NEW["required_credit"], CREDIT))

# ---- R7 . THE TEN EXISTING RECORDS MUST BE UNTOUCHED ----------------------
records.append(NEW)
if json.dumps(records[:10], sort_keys=True) != before:
    die("an existing rights record changed. This builder appends one record "
        "and alters nothing else.")
if len(records) != 11:
    die("expected 11 records after the append, found %d." % len(records))

if CHECK:
    print("CHECK ONLY — nothing written. 11 records would result.")
    sys.exit(0)

RECORDS.write_text(
    json.dumps(doc, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print("TANKTRIBE RIGHTS RECORD")
print("=" * 74)
print("  ok    8 guards passed")
print("  ok    appended 1 record; 11 total")
print("  ok    scope: %s + %s%s" % (DOMAIN, CDN_HOST, CDN_PREFIX))
print("  ok    AI-labelled asset exclusion recorded as a condition")
print("-" * 74)
print("wrote " + str(RECORDS))
print("NEXT: python3 .github/scripts/generate_image_rights_manifest.py")
