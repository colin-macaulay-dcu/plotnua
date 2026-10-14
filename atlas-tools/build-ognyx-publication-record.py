#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BOUNDED BUILDER — OGNYX: FROM PREVIEW-SCOPED RECORD TO PUBLICATION RECORD.

Founder decision, 14 October 2026: "PROCEED. Fabian at OGNYX has given PlotNua
the green light to feature the company and its products." The founder also
asked for the exact scope to be established from the ORIGINAL correspondence,
not from any later reading of it. This builder writes that scope, and nothing
wider.

THE EVIDENCE (Gmail thread 1a0fd83e5f6c284f, read 14 Oct 2026)
  2 Oct  PlotNua (1a0fd83e5f6c284f) asks to feature OGNYX and use selected
         imagery; offers a private preview.
  2 Oct  OGNYX (1a0fe3d7b43366cf): "Before proceeding, we would be interested
         in seeing the preview of how OGNYX would be presented within PlotNua."
  2 Oct  PlotNua (1a0fe99ef44b3eb8) sends the preview: "a simple YES is enough
         for us to proceed with featuring OGNYX and using the selected imagery
         shown in the preview, with clear credit and a link back".
  12 Oct PlotNua (1a1303acc64d5590): "If you're happy for us to feature OGNYX
         and use the selected product images shown there (where you have the
         rights to authorise their use), a simple YES is perfect."
  13 Oct OGNYX (1a13699d55beb7f9): "We have reviewed your offer and can confirm
         we would be happy to proceed with this. ... Please let us know once
         this is launched and we can see our products on your page."

WHAT THAT SUPPORTS, AND WHAT IT DOES NOT
  * feature OGNYX and its products publicly          -> permission.scope "feature"
  * the four selected images shown in the preview     -> permission.scope "imagery",
    and ONLY those four, enumerated in approved_assets   by enumeration, per asset
  * the pre-live review OGNYX asked for on 2 Oct was  -> listing_review CONFIRMED,
    satisfied: they reviewed it and confirmed           confirmed_at 2026-10-13
  * NOT any other OGNYX image, NOT any health, VAT, delivery, installation or
    lead-time claim, NOT any endorsement wording.

  The 14 Oct morning reading limited the four images to ognyx-preview.html.
  That was PlotNua's own restraint, not a limit OGNYX placed on the grant; the
  founder lifted it today on the original words. No founder EXCEPTION is used:
  every gate condition is met on evidence, so none needs waiving.

WRITES
  image-rights-records.json          the OGNYX row (gate fields, conditions,
                                     approved_assets); every other row untouched
  atlas-tools/preview-only-suppliers.json
                                     OGNYX graduates out of the register, exactly
                                     as Irish Sauna Company did on 10 Oct 2026
  (then run .github/scripts/generate_image_rights_manifest.py)

GUARDS
  O1 every other rights row is byte-identical in substance
  O2 exactly four approved assets, all on ognyx.com/cdn/shop/files/, each
     named in the Atlas Assets table, each with alt text, two labelled
     visualisations
  O3 the gate derives PUBLISHABLE on evidence alone: no founder_exception
  O4 the register no longer lists OGNYX and records why it left

  python3 atlas-tools/build-ognyx-publication-record.py [--check]
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
RECORDS = ROOT / "image-rights-records.json"
REGISTER = ROOT / "atlas-tools" / "preview-only-suppliers.json"
CHECK = "--check" in sys.argv
PREFIX = "https://www.ognyx.com/cdn/shop/files/"

PERMISSION = {
    "state": "GRANTED",
    "ref": "WELLNESS-FIRST-OGNYX-20261002",
    "record": "recIjRDMQ55nk6cOn",
    "date": "2026-10-13",
    "scope": ["feature", "imagery"],
    "conditions": ["four-named-images-only", "credit", "link-back",
                   "visualisations-labelled", "unmodified-hotlink",
                   "withdrawable-on-request"],
    "asked": ("If you're happy for us to feature OGNYX and use the selected "
              "product images shown there (where you have the rights to "
              "authorise their use), a simple YES is perfect. "
              "(PlotNua, 12 Oct 2026, Gmail 1a1303acc64d5590)"),
    "answered": ("We have reviewed your offer and can confirm we would be happy "
                 "to proceed with this. ... Please let us know once this is "
                 "launched and we can see our products on your page. "
                 "(OGNYX, 13 Oct 2026, Gmail 1a13699d55beb7f9)"),
    "note": ("Founder decision 14 Oct 2026: PROCEED, scope established from the "
             "original correspondence. Featuring OGNYX and its products is "
             "permitted; imagery is permitted for the four selected images "
             "shown in the preview and no others, by enumeration in "
             "approved_assets. Supersedes the 14 Oct morning reading that "
             "confined those images to ognyx-preview.html, which was PlotNua's "
             "own restraint, not OGNYX's."),
}
LISTING_REVIEW = {
    "state": "CONFIRMED",
    "requested_by": "supplier",
    "requested_in": "Gmail 1a0fe3d7b43366cf, 2 Oct 2026: \"Before proceeding, "
                    "we would be interested in seeing the preview\"",
    "confirmed_at": "2026-10-13",
    "confirmed_in": "Gmail 1a13699d55beb7f9",
    "note": ("OGNYX asked to see the presentation before proceeding, reviewed "
             "the preview sent on 2 Oct (re-sent 9 and 12 Oct) and confirmed "
             "on 13 Oct. The public listing is a subset of the range in that "
             "preview: twelve products whose own pages contradict themselves "
             "are held in Atlas (Standards = BLOCKED) and are not published."),
}
ASSET_APPROVAL = {
    "state": "SELECTED_ASSETS_APPROVED",
    "default_for_unlisted": "NOT_AUTHORISED",
    "approved_count": 4,
    "authorised_by": "OGNYX, 13 Oct 2026 (Gmail 1a13699d55beb7f9); founder "
                     "decision 14 Oct 2026",
    "note": ("Approval is by ENUMERATION, per asset. An OGNYX image is usable "
             "because it appears in approved_assets, never because it is served "
             "from ognyx.com. atlas-tools/prove-ognyx-imagery-containment.mjs "
             "refuses any other OGNYX image on any page."),
    "conditions_on_every_use": [
        "Credit: © OGNYX",
        "A working link to https://www.ognyx.com/",
        "The two visualisations are labelled as visualisations",
        "Hot-linked unmodified; never downloaded, rehosted, cropped or altered",
    ],
}
APPROVED_ASSETS = [
    {"url": PREFIX + "Screenshot2025-08-13at21.01.07.png?v=1755111942&width=1024",
     "product_code": "PROD-001217",
     "product_name": "OGNYX Stainless Steel Cold Plunge Tub for One",
     "atlas_asset": "recdcMBs7onIACLiO", "kind": "photograph", "primary": True,
     "alt": "Photograph of the OGNYX stainless steel cold plunge tub, clad in "
            "vertical timber staves with two steel hoops and a stainless inner "
            "rim, standing on gravel with a timber step stool beside it"},
    {"url": PREFIX + "Screenshot2025-08-13at21.01.20.png?v=1755111942&width=1024",
     "product_code": "PROD-001217",
     "product_name": "OGNYX Stainless Steel Cold Plunge Tub for One",
     "atlas_asset": "recOfcMW6ZjQh8PHj", "kind": "photograph", "primary": False,
     "alt": "Photograph looking down into the same empty cold plunge tub, "
            "showing the stainless steel interior, the timber staves and the "
            "two steel hoops, on gravel"},
    {"url": PREFIX + "Screenshot2025-08-11at18.27.16_33889bd3-cb18-4369-83b3-"
                     "b0be9a8d8586.png?v=1754936822&width=1024",
     "product_code": "PROD-001257",
     "product_name": "OGNYX 1,6m Outdoor Sauna for 3 people",
     "atlas_asset": "reczY9wkymWQg9df3", "kind": "visualisation", "primary": True,
     "alt": "Visualisation of the OGNYX 1.6m outdoor barrel sauna on a timber "
            "deck in a garden, with a glass door, a dark shingled roof and "
            "garden furniture beside it"},
    {"url": PREFIX + "Screenshot2025-08-12at19.20.47.png?v=1755025372&width=1024",
     "product_code": "PROD-001232",
     "product_name": "OGNYX Round Hot Tub with integrated wood-fired stove for 5 people",
     "atlas_asset": "reccvs54yEV48AY7R", "kind": "visualisation", "primary": True,
     "alt": "Visualisation of the OGNYX round hot tub, clad in timber with a "
            "stainless chimney rising from the integrated stove inside it and a "
            "timber step stool alongside, beside a swimming pool"},
]
CONDITIONS = [
    "FEATURE: PlotNua may feature OGNYX and its products publicly (OGNYX, 13 Oct "
    "2026, Gmail 1a13699d55beb7f9, answering the 12 Oct ask 1a1303acc64d5590 to "
    "\"feature OGNYX and use the selected product images shown there\").",
    "IMAGES: the four images enumerated in approved_assets and NO OTHER OGNYX "
    "image, on any page. Enforced per asset by "
    "atlas-tools/prove-ognyx-imagery-containment.mjs.",
    "Credit '© OGNYX' and a link back to https://www.ognyx.com/ wherever an "
    "image appears; the two visualisations are labelled as visualisations.",
    "Images are used unmodified and served from OGNYX's own domain. Nothing is "
    "downloaded, re-hosted, cropped or altered.",
    "No health, VAT, delivery, installation or lead-time claim is made for OGNYX "
    "products, and no wording implies endorsement or recommendation.",
    "OGNYX may request change or removal at any time, and PlotNua complies.",
    "No resale, no sublicensing, no unrelated advertising use. OGNYX retain "
    "ownership of the imagery.",
]
NOTE = (
    "SCOPE: ognyx.com only; OGNYX serve their product images from their own "
    "domain, so no delivery host is declared.\n\n14 OCTOBER 2026 — PUBLICATION "
    "RECORD. Founder decision: PROCEED. The scope above is taken from the "
    "original correspondence (see permission.asked / permission.answered). This "
    "row was preview-scoped until today; it now authorises featuring OGNYX and "
    "the four enumerated images. OGNYX left atlas-tools/preview-only-suppliers.json "
    "on the same day (see its graduated_to_full_grant list). Twelve products "
    "whose own pages contradict themselves stay held in Atlas and are not "
    "published.")
EVIDENCE_ADD = (
    " PUBLICATION RECORD, 14 October 2026: the founder decided to PROCEED on the "
    "original words of the 12 October ask (\"feature OGNYX and use the selected "
    "product images shown there\") and OGNYX's 13 October reply (\"happy to "
    "proceed ... let us know once this is launched and we can see our products "
    "on your page\"). The four images are no longer confined to the preview.")
GRADUATION = {
    "name": "OGNYX",
    "removed": "2026-10-14",
    "was": "imagery_mode 'preview-only' -- four images invited for "
           "ognyx-preview.html while publication was withheld.",
    "why_removed": ("OGNYX answered the 12 October 2026 ask to \"feature OGNYX "
                    "and use the selected product images shown there\" with "
                    "\"We have reviewed your offer and can confirm we would be "
                    "happy to proceed with this\" (13 Oct 2026, Gmail "
                    "1a13699d55beb7f9). The founder decided on 14 October 2026 "
                    "to proceed on those words. That is a publication grant, so "
                    "under this register's own rule (the_grant_boundary) the row "
                    "does not belong here any more."),
    "what_constrains_them_now": ("image-rights-records.json (approved_assets: "
                                 "exactly four images, by enumeration) and "
                                 "atlas-tools/prove-ognyx-imagery-containment.mjs, "
                                 "which refuses any other OGNYX image on any "
                                 "page and requires the credit, the link back "
                                 "and the visualisation labels wherever one "
                                 "appears. The publication gate derives "
                                 "PUBLISHABLE on evidence, with no founder "
                                 "exception."),
    "atlas_permission_ref": "WELLNESS-FIRST-OGNYX-20261002",
}


def die(m):
    print("REFUSED: " + m)
    sys.exit(2)


def main():
    doc = json.loads(RECORDS.read_text(encoding="utf-8"))
    rows = doc["records"]
    idx = [i for i, r in enumerate(rows) if r.get("organisation_name") == "OGNYX"]
    if len(idx) != 1:
        die("O1 expected exactly one OGNYX rights row")
    before_others = [json.dumps(r, sort_keys=True) for j, r in enumerate(rows) if j != idx[0]]
    row = rows[idx[0]]
    if row.get("organisation_record") != "recGxi1agXCBR1FLt":
        die("O1 the OGNYX row is not Atlas Organisation recGxi1agXCBR1FLt")

    row["permission"] = PERMISSION
    row["listing_review"] = LISTING_REVIEW
    row["asset_approval_state"] = "APPROVED"
    row["asset_approval"] = ASSET_APPROVAL
    row["approved_assets"] = APPROVED_ASSETS
    row["conditions"] = CONDITIONS
    row["note"] = NOTE
    if EVIDENCE_ADD not in row["evidence"]:
        row["evidence"] = row["evidence"] + EVIDENCE_ADD
    row["public_visibility"] = "PUBLISHABLE"
    row["hold_reason"] = None
    row.pop("founder_exception", None)

    # O1
    after_others = [json.dumps(r, sort_keys=True) for j, r in enumerate(rows) if j != idx[0]]
    if before_others != after_others:
        die("O1 another rights row changed")
    # O2
    urls = [a["url"] for a in APPROVED_ASSETS]
    if len(urls) != 4 or len(set(urls)) != 4 or not all(u.startswith(PREFIX) for u in urls):
        die("O2 the approved assets are not exactly four distinct ognyx.com files")
    if sorted(a["kind"] for a in APPROVED_ASSETS) != ["photograph", "photograph",
                                                      "visualisation", "visualisation"]:
        die("O2 two photographs and two visualisations expected")
    for a in APPROVED_ASSETS:
        if not a["atlas_asset"].startswith("rec") or len(a["alt"]) < 40:
            die("O2 asset without an Atlas record or alt text: " + a["url"])
        if a["kind"] == "visualisation" and not a["alt"].startswith("Visualisation"):
            die("O2 a visualisation's alt text does not say so")
    # O3
    if row.get("founder_exception") or "founder_exception" in json.dumps(row):
        die("O3 a founder exception would be doing the work evidence must do")

    # THE REGISTER IS EDITED AS TEXT. Its rows mix literal and \\u-escaped
    # characters, so a json.dumps round trip would rewrite every other row.
    cur_register = REGISTER.read_text(encoding="utf-8")
    new_register = cur_register
    start = new_register.find('    {\n      "name": "OGNYX",\n',
                              new_register.index('"suppliers": ['))
    if start >= 0:
        end = new_register.index('\n    }', start) + len('\n    }')
        if new_register[end:end + 2] == ",\n":
            new_register = new_register[:start] + new_register[end + 2:]
        else:
            die("O4 the OGNYX row is not followed by another row")
        grad = "    " + json.dumps(GRADUATION, indent=2, ensure_ascii=True).replace("\n", "\n    ")
        anchor = '\n    }\n  ],\n  "suppliers": ['
        if new_register.count(anchor) != 1:
            die("O4 graduated_to_full_grant anchor not found exactly once")
        new_register = new_register.replace(anchor, "\n    },\n" + grad + "\n  ],\n  \"suppliers\": [", 1)
    reg = json.loads(new_register)
    # O4
    if any(s.get("name") == "OGNYX" for s in reg["suppliers"]):
        die("O4 OGNYX still in the preview-only register")
    if [g.get("name") for g in reg["graduated_to_full_grant"]].count("OGNYX") != 1:
        die("O4 the register does not record why OGNYX left")

    new_records = json.dumps(doc, indent=2, ensure_ascii=False) + "\n"
    cur_records = RECORDS.read_text(encoding="utf-8")
    if CHECK:
        stale = [p.name for p, a, b in ((RECORDS, new_records, cur_records),
                                        (REGISTER, new_register, cur_register)) if a != b]
        if stale:
            print("CHECK FAILED: out of date: " + ", ".join(stale)); sys.exit(1)
        print("OGNYX publication record · CHECK OK — O1-O4 pass"); return
    RECORDS.write_text(new_records, encoding="utf-8")
    REGISTER.write_text(new_register, encoding="utf-8")
    print("OGNYX publication record · APPLIED — O1-O4 pass")


if __name__ == "__main__":
    main()
