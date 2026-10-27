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
  27 Oct Brona asked PlotNua to feature ISC's own Irish-made Island
         Collection "instead of the previously listed range" and wrote
         "Please feel free to use the product imagery and information from the
         collection" (1a17c9a56ea0fdca). Founder approved the replacement the
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

ÖÖD HOUSE (Gmail thread 1a088713c8eccf73) — added 14 Oct 2026 on the founder's
clarification ("ÖÖD correspondence"), a garden-room maker, recorded here so
every explicit publication state lives in one bounded builder.
  9 Sep  PlotNua told ÖÖD it had "included published information about ...
         ÖÖD House" and asked "for permission to use a small selection of your
         product photographs on PlotNua so homeowners can see the actual
         buildings alongside the information we hold about them", own products
         only, ÖÖD identified, unaltered, no implied endorsement,
         recommendation or residential suitability, displayed on plotnua.ie;
         "If you already have a ... image library ..., a link to that is
         perfect" (1a08876b76df3f50).
  14 Oct Gertrud Ots, Head of Marketing, answered that request (quoted
         beneath) with ÖÖD's photo library by product (1a139105565814d0).
  14 Oct Keir Tetsmann answered PlotNua's two Irish questions
         (1a13a4b45780ba3b). Neither asked to review anything.
  SCOPE, AND NO WIDER: featuring ÖÖD's products with PlotNua's information,
  and displaying photographs from that library on plotnua.ie for the model
  each shows. Not social media, advertising, redistribution or alteration.
  LISTING REVIEW: NOT_REQUIRED. ÖÖD did not ask for one. PlotNua OFFERED a
  private preview on 14 Oct (1a13993898984e9b); the offer was not taken up,
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
}


def assets_digest(a):
    return hashlib.sha256(json.dumps(a, sort_keys=True, ensure_ascii=False).encode("utf-8")).hexdigest()

ROWS = {
    "ÖÖD House": {
        "permission": {
            "state": "GRANTED", "ref": "IPO-007", "record": "recqvHdcTwNdBRszM",
            "date": "2026-10-14",
            "scope": ["feature", "imagery"],
            "conditions": ["own-products-only", "plotnua-ie-only", "credit", "link-back",
                           "unmodified-hotlink", "right-model-only",
                           "no-implied-endorsement-recommendation-or-residential-suitability",
                           "no-advertising-redistribution-or-resale", "withdrawable-on-request"],
            "asked": "PlotNua, 9 Sep 2026 (Gmail 1a08876b76df3f50): having \"included published "
                     "information about ... ÖÖD House\", asked \"for permission to use a small "
                     "selection of your product photographs on PlotNua so homeowners can see the "
                     "actual buildings alongside the information we hold about them\"; own "
                     "products only, ÖÖD identified, unaltered, displayed on plotnua.ie.",
            "answered": "\"Here you can find our photos by products: "
                        "https://drive.google.com/drive/folders/1Lm1aTPvVA_WkEEy4rBJsZ8zSa_mYbEPj\" "
                        "(Gertrud Ots, Head of Marketing, 14 Oct 2026, Gmail 1a139105565814d0, "
                        "replying to the request quoted beneath it)",
            "note": "Reconciled 14 Oct 2026 against the correspondence. 'feature' rests on the "
                    "request's own premise (PlotNua's information about ÖÖD, shown with the "
                    "photographs), which ÖÖD answered by supplying the library; the 2 Oct YES "
                    "follow-up was not itself answered. Imagery remains scoped per Drive file in "
                    "permitted_delivery_hosts; no other image is covered.",
        },
        "listing_review": {
            "state": "NOT_REQUIRED", "requested_by": None, "requested_in": None,
            "note": "ÖÖD did not ask to review a listing (Gertrud 1a139105565814d0; Keir "
                    "1a13a4b45780ba3b). PlotNua offered a private preview on 14 Oct "
                    "(1a13993898984e9b); it was not requested or sent. Founder ruling, 14 Oct "
                    "2026: a private preview existing creates no supplier-review requirement.",
        },
    },
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
            "conditions": ["credit", "link-back", "collection-images-only",
                           "visualisations-labelled", "no-harvia-manufacturer-imagery"],
            "asked": "PlotNua asked to feature Irish Sauna Company and use selected imagery "
                     "from its website (Gmail 1a0fd83ddde922b1, 2 and 9 Oct 2026).",
            "answered": "\"we would be delighted for you to use our imagery and product on your "
                        "site\" (Irish Sauna Company, 9 Oct 2026, Gmail 1a1208b5549f0e23)",
            "note": "Recorded 14 Oct 2026. PlotNua's 12 Oct question about Harvia manufacturer "
                    "photographs (Gmail 1a13036feca9cc4b) was never answered, so no Harvia "
                    "image was ever enumerated. 27 Oct 2026: Irish Sauna Company withdrew the "
                    "Harvia range and asked PlotNua to feature its own Irish-made Island "
                    "Collection instead, writing \"Please feel free to use the product imagery "
                    "and information from the collection\" (Gmail 1a17c9a56ea0fdca). Imagery "
                    "is permitted for that collection only: eight enumerated product "
                    "visualisations, credited and linked.",
            "collection_grant": {
                "date": "2026-10-27", "gmail": "1a17c9a56ea0fdca", "thread": "1a0fd83ddde922b1",
                "from": "info@irishsaunacompany.com (Brona)",
                "asked_by_supplier": "would it be possible to update our listing on PlotNua to "
                                     "feature our new Irish-made collection instead of the "
                                     "previously listed range?",
                "verbatim": "Please feel free to use the product imagery and information from "
                            "the collection",
                "collection": "https://irishsaunacompany.com/collections/residential-outdoor-saunas-ireland",
                "scope": "The four products of that collection (The Clare, The Inis, The Aran, "
                         "The Skellig) and their product images as of 27 Oct 2026. NOT the "
                         "supplier's pods or mobile saunas, NOT any Harvia manufacturer "
                         "imagery, NOT any other company.",
                "founder_approval": "2026-10-27, 'Irish Sauna Company collection — "
                                    "implementation approved'",
            },
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
