#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BOUNDED BUILDER — EXPLICIT PUBLICATION STATES FOR TWO WELLNESS SUPPLIERS
WHOSE OWN WORDS ALREADY GRANT THEM: TANKTRIBE AND IRISH SAUNA COMPANY.

Founder brief, 14 October 2026 ("Garden Retreat — complete experience
restructure"): populate the Garden Retreat maker universe with every supplier
that meets PlotNua's publication requirements, using the established gate,
with no founder exceptions and no legacy-baseline additions.

Both rows already exist in image-rights-records.json with a live grant, but
predate the gate's fields, so the gate (correctly) holds them as
permission-state-missing. This builder records the explicit states their own
correspondence supports -- nothing wider -- so the gate can read evidence
instead of absence.

TANKTRIBE (Gmail thread 1a0fd832b4b384f2)
  2 Oct  asked to "feature Tanktribe and use selected imagery from its
         website", with credit and a link back; answered "YES"
         (1a0fd9de5ac55e40).
  8 Oct  shown the private preview; answered "yes all looks great thanks"
         (1a11bff8584a50b1).
IRISH SAUNA COMPANY (Gmail thread 1a0fd83ddde922b1)
  9 Oct  "we would be delighted for you to use our imagery and product on
         your site" (1a1208b5549f0e23).
  12 Oct shown the preview; "That looks great, I am happy for it to go."
         (1a12f28526374227).
  12 Oct PlotNua asked whether Harvia manufacturer photographs may be used
         (1a13036feca9cc4b). UNANSWERED. So no image is enumerated for
         publication: the listing is text only until that is settled.

Neither row gains approved_assets. Imagery is not extended by this builder.

  python3 atlas-tools/build-wellness-publication-records.py [--check]
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
RECORDS = ROOT / "image-rights-records.json"
CHECK = "--check" in sys.argv

ROWS = {
    "Tanktribe": {
        "permission": {
            "state": "GRANTED", "ref": "WELLNESS-FIRST-TANKTRIBE-20261002",
            "record": "recHf6UOaAVMmmoGA", "date": "2026-10-02",
            "scope": ["feature", "imagery"],
            "conditions": ["credit", "link-back", "selected-first-party-imagery-only"],
            "asked": "PlotNua asked on 2 Oct 2026 for permission to feature Tanktribe and use "
                     "selected imagery from its website, with credit and a link back "
                     "(Gmail 1a0fd832b4b384f2).",
            "answered": "\"YES\" (Tanktribe, 2 Oct 2026, Gmail 1a0fd9de5ac55e40)",
            "note": "Recorded 14 Oct 2026 from the supplier's own reply. Images are not "
                    "enumerated here, so no Tanktribe image is published by this record.",
        },
        "listing_review": {
            "state": "CONFIRMED", "requested_by": "plotnua",
            "requested_in": "Gmail 1a0fe7aaf1258126, 2 Oct 2026 (private preview sent)",
            "confirmed_at": "2026-10-08", "confirmed_in": "Gmail 1a11bff8584a50b1",
            "note": "\"yes all looks great thanks\" — Tanktribe on the private preview, 8 Oct 2026.",
        },
    },
    "Irish Sauna Company": {
        "permission": {
            "state": "GRANTED", "ref": "WELLNESS-FIRST-IRISH-SAUNA-COMPANY-20261002",
            "record": "recH6lssOAemyP9rz", "date": "2026-10-09",
            "scope": ["feature", "imagery"],
            "conditions": ["credit", "link-back", "no-third-party-manufacturer-imagery-until-confirmed"],
            "asked": "PlotNua asked to feature Irish Sauna Company and use selected imagery "
                     "from its website (Gmail 1a0fd83ddde922b1, 2 and 9 Oct 2026).",
            "answered": "\"we would be delighted for you to use our imagery and product on your "
                        "site\" (Irish Sauna Company, 9 Oct 2026, Gmail 1a1208b5549f0e23)",
            "note": "Recorded 14 Oct 2026. PlotNua's 12 Oct question about Harvia manufacturer "
                    "photographs (Gmail 1a13036feca9cc4b) is unanswered, so no image is "
                    "enumerated: the listing is text only.",
        },
        "listing_review": {
            "state": "CONFIRMED", "requested_by": "supplier",
            "requested_in": "Irish Sauna Company, 2 Oct 2026: happy to take a look at the "
                            "private preview first (Gmail 1a0fdc60270190fd)",
            "confirmed_at": "2026-10-12", "confirmed_in": "Gmail 1a12f28526374227",
            "note": "\"That looks great, I am happy for it to go.\" — Irish Sauna Company on the "
                    "private preview, 12 Oct 2026.",
        },
    },
}


def die(m):
    print("REFUSED: " + m); sys.exit(2)


def main():
    doc = json.loads(RECORDS.read_text(encoding="utf-8"))
    before = {r["organisation_name"]: json.dumps(r, sort_keys=True) for r in doc["records"]}
    for name, add in ROWS.items():
        rows = [r for r in doc["records"] if r.get("organisation_name") == name]
        if len(rows) != 1:
            die("expected exactly one %s rights row" % name)
        r = rows[0]
        if not str(r.get("permission_outcome", "")).startswith("Granted"):
            die("%s has no live grant to record states for" % name)
        if r.get("approved_assets") or r.get("founder_exception"):
            die("%s: this builder never touches imagery or exceptions" % name)
        r["permission"] = add["permission"]
        r["listing_review"] = add["listing_review"]
        r["public_visibility"] = "PUBLISHABLE"
        r["hold_reason"] = None
    for r in doc["records"]:
        if r["organisation_name"] not in ROWS and json.dumps(r, sort_keys=True) != before[r["organisation_name"]]:
            die("another rights row changed: " + r["organisation_name"])
    new = json.dumps(doc, indent=2, ensure_ascii=False) + "\n"
    cur = RECORDS.read_text(encoding="utf-8")
    if CHECK:
        if new != cur:
            print("CHECK FAILED: image-rights-records.json is out of date"); sys.exit(1)
        print("Wellness publication records · CHECK OK — Tanktribe, Irish Sauna Company"); return
    RECORDS.write_text(new, encoding="utf-8")
    print("Wellness publication records · APPLIED — Tanktribe, Irish Sauna Company")


if __name__ == "__main__":
    main()
