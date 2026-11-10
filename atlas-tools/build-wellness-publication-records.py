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

TANKTRIBE (correspondence held privately: PN-EVID-RIGHTS-TANKTRIBE-*)
  2 Oct  asked by email to feature Tanktribe and use selected imagery from
         its website, with credit and a link back; answered YES.
  8 Oct  shown the private preview; confirmed it by email.
IRISH SAUNA COMPANY (held privately: PN-EVID-RIGHTS-IRISH-SAUNA-COMPANY-*)
  9 Oct  granted use of its imagery and products on PlotNua, by email.
  12 Oct shown the preview; approved it for publication by email.
  12 Oct PlotNua asked whether Harvia manufacturer photographs may be used.
         UNANSWERED. So no image is enumerated for
         publication: the listing is text only until that is settled.
  27 Oct Irish Sauna Company asked PlotNua to feature its own Irish-made
         Island Collection instead of the previously listed range, and gave
         permission to use the product imagery and information from the
         collection. Founder approved the replacement the
         same day. The Harvia question is moot: that range is withdrawn. The
         eight collection images are enumerated by
         atlas-tools/build-irish-sauna-company-collection-record.py, pinned
         by digest below; this builder still never adds imagery itself.

Neither row gains approved_assets. Imagery is not extended by this builder.
(27 Oct 2026: the Irish Sauna Company Island Collection set is written by
atlas-tools/build-irish-sauna-company-collection-record.py and pinned below.)
(16 Oct 2026: Tanktribe's four photographs were enumerated separately in the
authorised imagery commit 15b145e. This builder preserves that exact set,
pinned by digest below, and refuses any other imagery on any row.)

ÖÖD HOUSE (held privately: PN-EVID-RIGHTS-ORG-000149-20261014) — added
14 Oct 2026 on the founder's clarification, a garden-room maker, recorded here
so every explicit publication state lives in one bounded builder.
  9 Sep  PlotNua told ÖÖD it had included published information about ÖÖD
         House and asked, by email, for permission to use a small selection
         of ÖÖD's product photographs on PlotNua alongside that information:
         own products only, ÖÖD identified, unaltered, no implied
         endorsement, recommendation or residential suitability, displayed on
         plotnua.ie; a link to an existing image library would do.
  14 Oct ÖÖD answered that request by email with its photo library by
         product.
  14 Oct ÖÖD separately answered PlotNua's two Irish questions by email.
         Neither reply asked to review anything.
  SCOPE, AND NO WIDER: featuring ÖÖD's products with PlotNua's information,
  and displaying photographs from that library on plotnua.ie for the model
  each shows. Not social media, advertising, redistribution or alteration.
  LISTING REVIEW: NOT_REQUIRED. ÖÖD did not ask for one. PlotNua OFFERED a
  private preview on 14 Oct; the offer was not taken up,
  and the founder ruled on 14 Oct that a private preview existing creates no
  review requirement. The imagery stays scoped per Drive file (unchanged).

  python3 atlas-tools/build-wellness-publication-records.py [--check]
"""
import hashlib
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
RECORDS = ROOT / "image-rights-records.json"
CHECK = "--check" in sys.argv

# Imagery already authorised OUTSIDE this builder (15b145e, 16 Oct 2026).
# Preserved untouched. Any other approved_assets value, on any row, refuses.
AUTHORISED_ASSETS = {
    "Tanktribe": "86034976a18addd30b801f4c048801e4b8c462d1f79b45838af7436a0bffe251",
    # 27 Oct 2026: the eight Island Collection product visualisations, written by
    # atlas-tools/build-irish-sauna-company-collection-record.py.
    "Irish Sauna Company": "9f4334b66b554adc5c67669b75ee66746a099ec18e50948a78899000a8c433e2",
}


def assets_digest(a):
    return hashlib.sha256(json.dumps(a, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()

ROWS = {
    "ÖÖD House": {
        "permission": {
            "state": "GRANTED",
            "pre_live_review_requested": False,
            "ref": "IPO-007",
            "record": "recqvHdcTwNdBRszM",
            "date": "2026-10-14",
            "scope": ["feature", "imagery"],
            "conditions": ["own-products-only", "plotnua-ie-only", "credit", "link-back", "unmodified-hotlink", "right-model-only", "no-implied-endorsement-recommendation-or-residential-suitability", "no-advertising-redistribution-or-resale", "withdrawable-on-request"],
            "asked": "PlotNua, by email 9 Sep 2026: having included published information about ÖÖD House, asked for permission to use a small selection of ÖÖD's product photographs on PlotNua so homeowners can see the actual buildings alongside that information; own products only, ÖÖD identified, unaltered, displayed on plotnua.ie.",
            "answered": "ÖÖD House, by email 14 Oct 2026, replying to that request: supplied a library of its photographs organised by product. Wording and library link held privately (PN-EVID-RIGHTS-ORG-000149-20261014).",
            "note": "Reconciled 14 Oct 2026 against the correspondence. 'feature' rests on the request's own premise (PlotNua's information about ÖÖD, shown with the photographs), which ÖÖD answered by supplying the library; the 2 Oct YES follow-up was not itself answered. Imagery remains scoped per Drive file in permitted_delivery_hosts; no other image is covered.",
        },
        "listing_review": {
            "state": "NOT_REQUIRED",
            "requested_by": None,
            "requested_in": None,
            "note": "ÖÖD did not ask to review a listing (its replies of 14 Oct 2026). PlotNua offered a private preview on 14 Oct; it was not requested or sent. Founder ruling, 14 Oct 2026: a private preview existing creates no supplier-review requirement.",
        },
    },
    "Tanktribe": {
        "permission": {
            "state": "GRANTED",
            "pre_live_review_requested": False,
            "ref": "WELLNESS-FIRST-TANKTRIBE-20261002",
            "record": "recHf6UOaAVMmmoGA",
            "date": "2026-10-02",
            "scope": ["feature", "imagery"],
            "conditions": ["credit", "link-back", "selected-first-party-imagery-only"],
            "asked": "PlotNua asked by email on 2 Oct 2026 for permission to feature Tanktribe and use selected imagery from its website, with credit and a link back.",
            "answered": "YES (Tanktribe, by email, 2 Oct 2026; wording held privately, PN-EVID-RIGHTS-TANKTRIBE-20261002)",
            "note": "Recorded 14 Oct 2026 from the supplier's own reply. Images are not enumerated here, so no Tanktribe image is published by this record.",
        },
        "listing_review": {
            "state": "CONFIRMED",
            "requested_by": "plotnua",
            "requested_in": "Email, 2 Oct 2026 (private preview sent)",
            "confirmed_at": "2026-10-08",
            "confirmed_in": "Email, 8 Oct 2026 (PN-EVID-RIGHTS-TANKTRIBE-20261008)",
            "note": "Tanktribe confirmed the private preview by email, 8 Oct 2026.",
        },
    },
    "Irish Sauna Company": {
        "permission": {
            "state": "GRANTED",
            "pre_live_review_requested": True,
            "ref": "WELLNESS-FIRST-IRISH-SAUNA-COMPANY-20261002",
            "record": "recH6lssOAemyP9rz",
            "date": "2026-10-09",
            "scope": ["feature", "imagery"],
            "conditions": ["credit", "link-back", "collection-images-only", "visualisations-labelled", "no-harvia-manufacturer-imagery"],
            "asked": "PlotNua asked by email to feature Irish Sauna Company and use selected imagery from its website (2 and 9 Oct 2026).",
            "answered": "Irish Sauna Company, by email 9 Oct 2026: PlotNua may use its imagery and products on its site. Wording held privately (PN-EVID-RIGHTS-IRISH-SAUNA-COMPANY-20261009).",
            "note": "Recorded 14 Oct 2026. PlotNua's 12 Oct question about Harvia manufacturer photographs was never answered, so no Harvia image was ever enumerated. 27 Oct 2026: Irish Sauna Company withdrew the Harvia range and asked PlotNua to feature its own Irish-made Island Collection instead, giving permission to use the product imagery and information from the collection (PN-EVID-RIGHTS-IRISH-SAUNA-COMPANY-20261027). Imagery is permitted for that collection only: eight enumerated product visualisations, credited and linked.",
            "collection_grant": {
                "date": "2026-10-27",
                "evidence_ref": "PN-EVID-RIGHTS-IRISH-SAUNA-COMPANY-20261027",
                "from": "Irish Sauna Company, by email",
                "asked_by_supplier": "asked PlotNua to update its listing to feature the new Irish-made collection instead of the previously listed range",
                "granted": "permission to use the product imagery and information from the collection (wording held privately)",
                "collection": "https://irishsaunacompany.com/collections/residential-outdoor-saunas-ireland",
                "scope": "The four products of that collection (The Clare, The Inis, The Aran, The Skellig) and their product images as of 27 Oct 2026. NOT the supplier's pods or mobile saunas, NOT any Harvia manufacturer imagery, NOT any other company.",
                "founder_approval": "2026-10-27, 'Irish Sauna Company collection — implementation approved'",
            },
        },
        "listing_review": {
            "state": "CONFIRMED",
            "requested_by": "supplier",
            "requested_in": "Irish Sauna Company, by email 2 Oct 2026: asked to see the private preview first",
            "confirmed_at": "2026-10-12",
            "confirmed_in": "Email, 12 Oct 2026 (PN-EVID-RIGHTS-IRISH-SAUNA-COMPANY-20261012)",
            "note": "Irish Sauna Company approved the private preview for publication by email, 12 Oct 2026.",
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
        if r.get("founder_exception"):
            die("%s: this builder never touches imagery or exceptions" % name)
        assets = r.get("approved_assets")
        if assets and assets_digest(assets) != AUTHORISED_ASSETS.get(name):
            die("%s: approved_assets are not the authorised set; this builder never "
                "touches imagery or exceptions" % name)
        assets_before = json.dumps(assets, sort_keys=True)
        r["permission"] = add["permission"]
        r["listing_review"] = add["listing_review"]
        r["public_visibility"] = "PUBLISHABLE"
        r["hold_reason"] = None
        if json.dumps(r.get("approved_assets"), sort_keys=True) != assets_before:
            die("%s: approved_assets changed during the build" % name)
    for r in doc["records"]:
        if r["organisation_name"] not in ROWS and json.dumps(r, sort_keys=True) != before[r["organisation_name"]]:
            die("another rights row changed: " + r["organisation_name"])
    new = json.dumps(doc, indent=2, ensure_ascii=False) + "\n"
    cur = RECORDS.read_text(encoding="utf-8")
    if CHECK:
        # The trailing newline alone is not content (15b145e saved the file
        # without one); everything else must match byte for byte.
        if new.rstrip("\n") != cur.rstrip("\n"):
            print("CHECK FAILED: image-rights-records.json is out of date"); sys.exit(1)
        print("Publication records · CHECK OK — " + ", ".join(ROWS)); return
    RECORDS.write_text(new, encoding="utf-8")
    print("Publication records · APPLIED — " + ", ".join(ROWS))


if __name__ == "__main__":
    main()
