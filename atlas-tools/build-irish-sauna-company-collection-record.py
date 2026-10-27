#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BOUNDED BUILDER — IRISH SAUNA COMPANY ISLAND COLLECTION IMAGERY RECORD.

Founder approval, 27 October 2026 ("Irish Sauna Company collection —
implementation approved"): replace the two live Harvia products with the
supplier's own Irish-made Island Collection (The Clare, The Inis, The Aran,
The Skellig) and use eight approved collection images, two per sauna,
displayed as "Product visualisation", credited "© Irish Sauna Company" and
linked to the supplier.

THE EVIDENCE. Brona, info@irishsaunacompany.com, 27 Oct 2026 09:04 UTC,
Gmail 1a17c9a56ea0fdca (thread 1a0fd83ddde922b1):
  "would it be possible to update our listing on PlotNua to feature our new
   Irish-made collection instead of the previously listed range?"
  "Please feel free to use the product imagery and information from the
   collection"
The permission itself (scope, conditions, collection_grant) is written by
atlas-tools/build-wellness-publication-records.py, which owns every wellness
publication state. THIS builder writes only the imagery enumeration that
permission allows, and nothing wider:

  * exactly eight images, two for each of the four Atlas products
    PROD-001331..PROD-001334, each tied to its Atlas Asset record;
  * every image a VISUALISATION. The collection's images are computer-
    generated studio renders (no camera data; the products launched 25-27 Oct
    and are made to order). They are never described as photographs of a
    completed installation: kind "visualisation", alt text opening
    "Visualisation", display label "Product visualisation";
  * served unmodified from the supplier's own domain
    (https://irishsaunacompany.com/cdn/shop/files/...), inside the record's
    permitted_domain. No Shopify CDN host is declared, so none is authorised;
  * the floor-plan views and the "Clare vs a garden shed" infographic are
    NOT enumerated, and nothing outside the collection is (pods, mobile
    saunas, any Harvia manufacturer image, any other company).

Checks, each refusing the build:
  I1  exactly one Irish Sauna Company row, Atlas Organisation recLW0vZbkBGPRkZ9,
      and no other rights row changes;
  I2  the permission written by the wellness builder carries the 27 Oct
      collection grant (Gmail 1a17c9a56ea0fdca) and scope feature + imagery;
  I3  eight distinct URLs on irishsaunacompany.com/cdn/shop/files/, two per
      product code, one primary each, all visualisations with alt text
      opening "Visualisation", each with an Atlas Asset record;
  I4  no founder exception does the work evidence must do.

    python3 atlas-tools/build-irish-sauna-company-collection-record.py           apply
    python3 atlas-tools/build-irish-sauna-company-collection-record.py --check   verify
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RECORDS = ROOT / "image-rights-records.json"
REGISTER = ROOT / "atlas-tools" / "preview-only-suppliers.json"
CHECK = "--check" in sys.argv
ORG_ID = "recLW0vZbkBGPRkZ9"
PREFIX = "https://irishsaunacompany.com/cdn/shop/files/"
CODES = {"PROD-001331": "The Clare | 1–2 Person Garden Sauna",
         "PROD-001332": "The Inis | 2–4 Person Garden Sauna",
         "PROD-001333": "The Aran | 4–6 Person Luxury Garden Sauna",
         "PROD-001334": "The Skellig | Luxury 6–8 Person Garden Sauna"}


def asset(file, code, rec, primary, alt):
    return {"url": PREFIX + file + "?width=1024", "product_code": code, "product_name": CODES[code],
            "atlas_asset": rec, "kind": "visualisation", "primary": primary, "alt": alt,
            "display_label": "Product visualisation"}


APPROVED_ASSETS = [
    asset("1-2-PersonSauna-Front-View.png", "PROD-001331", "recpt4Qq6NPz95fWM", True,
          "Visualisation of The Clare from the front: a compact black-clad garden sauna with a "
          "full-height glass door and a warm-lit Thermowood interior"),
    asset("1-2_Person_Sauna_-_White_Back_Ground.png", "PROD-001331", "recXNhcB54gi9SmXq", False,
          "Visualisation of The Clare at an angle with its glass door open, showing the Alder "
          "bench and Thermowood interior"),
    asset("2-4_Person_Garden_Sauna.png", "PROD-001332", "recnoZpQDkfooFP2v", True,
          "Visualisation of The Inis from the front: a black-clad garden sauna with a full-height "
          "glazed door and two tiers of lit Alder benches"),
    asset("2-4_Person_Insulated_Sauna.png", "PROD-001332", "recTCNM71LSYMSW4u", False,
          "Visualisation of The Inis at an angle with its glazed door open, showing the tiered "
          "Alder benches and Harvia wall heater"),
    asset("4-6_Person_Sauna_-_Front_View.png", "PROD-001333", "recd2xqlMd6qyKxhI", True,
          "Visualisation of The Aran from the front: a black-clad garden sauna with a large "
          "panoramic window, two-tier benches and a cylindrical heater"),
    asset("4-6_Person_Garaden_Sauna_-_Side_View.png", "PROD-001333", "reckdF69PkRdLNUHs", False,
          "Visualisation of The Aran at an angle, showing the panoramic front window and the "
          "glass entrance door on the right-hand side"),
    asset("TheSkellig-FrontView.png", "PROD-001334", "recFRo2HR5jSQ9qnG", True,
          "Visualisation of The Skellig from the front: a wide black-clad garden sauna with a "
          "large panoramic window and L-shaped two-tier benches"),
    asset("The_Skellig_Side_View.png", "PROD-001334", "recKjOUkGP623IS8K", False,
          "Visualisation of The Skellig at an angle, showing the panoramic window and the "
          "full-height glazed entrance door at the side"),
]
ASSET_APPROVAL = {
    "state": "SELECTED_ASSETS_APPROVED",
    "default_for_unlisted": "NOT_AUTHORISED",
    "approved_count": 8,
    "authorised_by": "Irish Sauna Company (Brona), 27 Oct 2026, Gmail 1a17c9a56ea0fdca; "
                     "founder approval 27 Oct 2026",
    "note": "Approval is by ENUMERATION, per asset: two product visualisations for each Island "
            "Collection sauna. An Irish Sauna Company image is usable because it appears in "
            "approved_assets, never because it is served from irishsaunacompany.com. Floor plans, "
            "the footprint infographic, pods, mobile saunas and any Harvia manufacturer image are "
            "not authorised.",
    "conditions_on_every_use": [
        "Credit: © Irish Sauna Company",
        "A working link to https://irishsaunacompany.com/",
        "Labelled 'Product visualisation'; never described as a photograph of a completed installation",
        "Hot-linked unmodified from irishsaunacompany.com; never downloaded, rehosted, cropped or altered",
    ],
}
CONDITIONS = [
    "FEATURE: PlotNua may feature Irish Sauna Company and its products (9 Oct 2026, Gmail "
    "1a1208b5549f0e23; listing approved 12 Oct, 1a12f28526374227).",
    "IMAGES: the eight Island Collection product visualisations enumerated in approved_assets "
    "(two per sauna) and NO OTHER Irish Sauna Company image, under the supplier's 27 Oct 2026 "
    "permission for 'the product imagery and information from the collection' (Gmail "
    "1a17c9a56ea0fdca). Pods, mobile saunas and any Harvia manufacturer image are excluded.",
    "Credit '© Irish Sauna Company' and a link back to https://irishsaunacompany.com/ wherever "
    "an image appears.",
    "Every image is a product visualisation (computer-generated render) and is labelled so; it "
    "is never described as a photograph of a completed installation.",
    "PROVENANCE: the Island Collection saunas may be described as designed and handcrafted to "
    "order by Irish Sauna Company in Connemara, Co. Galway, with heaters by Harvia. No PlotNua "
    "surface may imply every component is made in Ireland. The withdrawn Harvia range was never "
    "Irish-built and is not published.",
    "Images are used unmodified and served from the supplier's own domain; nothing is "
    "downloaded, re-hosted, cropped or altered. No Shopify CDN host is authorised.",
    "Irish Sauna Company may request change or removal at any time, and PlotNua complies.",
]
NOTE = ("27 OCTOBER 2026 — ISLAND COLLECTION. Irish Sauna Company withdrew the Harvia range "
        "(all three product pages now return 404) and asked PlotNua to feature its own Irish-made "
        "collection instead. Founder approved the replacement the same day. This row now "
        "enumerates eight collection images as product visualisations; the earlier Harvia "
        "photograph question (12 and 16 Oct) is moot and no Harvia image is used. Images are "
        "served from irishsaunacompany.com/cdn/shop/files/, inside permitted_domain, so no "
        "delivery host is declared. Written by "
        "atlas-tools/build-irish-sauna-company-collection-record.py.")
EVIDENCE_ADD = (" COLLECTION PERMISSION, 27 October 2026: Brona asked PlotNua to feature the new "
                "Irish-made collection \"instead of the previously listed range\" and wrote \"Please "
                "feel free to use the product imagery and information from the collection\" (Gmail "
                "1a17c9a56ea0fdca). Founder approved the replacement on 27 October 2026. Atlas Image "
                "Permission Outreach recH6lssOAemyP9rz records the 27 October scope.")
REG_OLD = ("irish-sauna-company-preview.html remains noindex and unlisted, and the grant has not "
           "been exercised on any other page.")
REG_NEW = ("irish-sauna-company-preview.html was retired on 27 Oct 2026 (it described the "
           "withdrawn Harvia range). Since 27 Oct 2026 the grant is exercised on the Garden "
           "Retreat maker explorer for the eight enumerated Island Collection product "
           "visualisations only (atlas-tools/build-irish-sauna-company-collection-record.py).")


def die(m):
    print("REFUSED: " + m)
    sys.exit(2)


def main():
    doc = json.loads(RECORDS.read_text(encoding="utf-8"))
    rows = doc["records"]
    idx = [i for i, r in enumerate(rows) if r.get("organisation_name") == "Irish Sauna Company"]
    if len(idx) != 1:
        die("I1 expected exactly one Irish Sauna Company rights row")
    before_others = [json.dumps(r, sort_keys=True) for j, r in enumerate(rows) if j != idx[0]]
    row = rows[idx[0]]
    if row.get("organisation_record") != ORG_ID:
        die("I1 the Irish Sauna Company row is not Atlas Organisation " + ORG_ID)
    perm = row.get("permission") or {}
    cg = perm.get("collection_grant") or {}
    if (perm.get("state") != "GRANTED" or sorted(perm.get("scope") or []) != ["feature", "imagery"]
            or cg.get("gmail") != "1a17c9a56ea0fdca" or "from the collection" not in cg.get("verbatim", "")):
        die("I2 the permission does not carry the 27 Oct 2026 collection grant; run "
            "atlas-tools/build-wellness-publication-records.py first")

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

    after_others = [json.dumps(r, sort_keys=True) for j, r in enumerate(rows) if j != idx[0]]
    if before_others != after_others:
        die("I1 another rights row changed")
    urls = [a["url"] for a in APPROVED_ASSETS]
    if len(urls) != 8 or len(set(urls)) != 8 or not all(u.startswith(PREFIX) for u in urls):
        die("I3 the approved assets are not exactly eight distinct irishsaunacompany.com files")
    for code in CODES:
        mine = [a for a in APPROVED_ASSETS if a["product_code"] == code]
        if len(mine) != 2 or sum(1 for a in mine if a["primary"]) != 1:
            die("I3 %s must carry exactly two images, one primary" % code)
    for a in APPROVED_ASSETS:
        if (a["kind"] != "visualisation" or not a["alt"].startswith("Visualisation")
                or a.get("display_label") != "Product visualisation"):
            die("I3 every collection image is a labelled visualisation: " + a["url"])
        if not a["atlas_asset"].startswith("rec") or len(a["atlas_asset"]) != 17 or len(a["alt"]) < 40:
            die("I3 asset without an Atlas record or alt text: " + a["url"])
    if "founder_exception" in json.dumps(row):
        die("I4 a founder exception would be doing the work evidence must do")

    cur_register = REGISTER.read_text(encoding="utf-8")
    new_register = cur_register
    if REG_OLD in new_register:
        if new_register.count(REG_OLD) != 1:
            die("I1 the preview register sentence is not unique")
        new_register = new_register.replace(REG_OLD, REG_NEW, 1)
    elif REG_NEW not in new_register:
        die("I1 the preview register does not describe Irish Sauna Company as expected")
    json.loads(new_register)

    new_records = json.dumps(doc, indent=2, ensure_ascii=False) + "\n"
    cur_records = RECORDS.read_text(encoding="utf-8")
    if CHECK:
        stale = [p.name for p, a, b in ((RECORDS, new_records, cur_records),
                                        (REGISTER, new_register, cur_register)) if a != b]
        if stale:
            print("CHECK FAILED: out of date: " + ", ".join(stale)); sys.exit(1)
        print("Irish Sauna Company collection record · CHECK OK — I1-I4 pass"); return
    RECORDS.write_text(new_records, encoding="utf-8")
    REGISTER.write_text(new_register, encoding="utf-8")
    print("Irish Sauna Company collection record · APPLIED — I1-I4 pass")


if __name__ == "__main__":
    main()
