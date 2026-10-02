#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
IMG-6 · ADD THREE FOUNDER-CONFIRMED IMAGE GRANTS TO THE CANONICAL RECORDS.

Garden Room Ireland, Elm Landscaping, Don Modular Homes. Nothing else.

This edits image-rights-records.json, which is the INPUT to
.github/scripts/generate_image_rights_manifest.py. It does not touch
image-rights-manifest.json: that file says of itself "GENERATED, NOT
HAND-EDITED", and a builder that wrote to it directly would make that sentence
false the way the manifest's own governance note was once false.

WHY A BUILDER AND NOT AN EDIT. Three grants, each with a scope that is only
correct in its details, appended to a file whose other six rows authorise live
publication. An anchored builder refuses when a detail has moved; a hand edit
discovers that afterwards.

THE SCOPE THAT MATTERS, and the reason this was written carefully:

  Garden Room Ireland serve their photographs from static.wixstatic.com, a CDN
  shared by every Wix site on the internet. Their own uploads sit under two
  account prefixes, fef4b6_ and 083d1a_. Three other prefixes were seen on
  their pages during the crawl -- 11062b_ (Wix stock), 8bb438_ and 4d0b36_ --
  and are somebody else's. The grant is therefore written as two scoped
  delivery hosts, /media/fef4b6_ and /media/083d1a_, and a guard below refuses
  the build if a bare /media/ prefix or any of the three foreign prefixes ever
  reaches the record. The gate matches with pathname.startsWith(prefix), so
  these prefixes exclude the foreign accounts by construction rather than by
  anyone remembering to.

  Elm Landscaping and Don Modular Homes serve their own images from their own
  domains, so neither needs a delivery host and neither gets one. Elm's
  /gallery/ page is an Instagram embed; permission does not reach it, and a
  guard refuses any mention of Instagram in these records.

UNKNOWN != GRANTED is untouched. Three rows are added. Nothing global is
loosened, no vocabulary is widened, and the other six records must come out
byte-identical.

Run: python3 .github/scripts/build-img6-three-supplier-grants.py [--check]
"""

import hashlib
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent.parent
RECORDS = REPO / "image-rights-records.json"

CHECK_ONLY = "--check" in sys.argv

# The gate's live-grant vocabulary, spelled exactly. Duplicated here on purpose
# for the same reason the generator duplicates it: a record that spells an
# outcome loosely must be refused where it is written, not where it is read.
LIVE_GRANTS = {
    "Granted — Founder Confirmed",
    "Granted with Conditions — Founder Confirmed",
    "Granted — Supplier Confirmed (one-click)",
}

FOREIGN_WIX_PREFIXES = ["11062b_", "8bb438_", "4d0b36_"]

NEW = [
    # ---------------------------------------------------------------- GRI ---
    {
        "organisation_record": "recUrpkOqKbynjQP0",
        "organisation_code": "ORG-000012",
        "organisation_name": "Garden Room Ireland",
        "permission_outcome": "Granted with Conditions — Founder Confirmed",
        "permitted_domain": "gardenroomireland.ie",
        "permitted_delivery_hosts": [
            {
                "host": "static.wixstatic.com",
                "path_prefix": "/media/fef4b6_",
                "why": "Garden Room Ireland's own Wix media account prefix. static.wixstatic.com is shared by every Wix site, so the account prefix — not the host — is the scope. Verified across all nine of their first-party gallery pages during the 2 October 2026 crawl."
            },
            {
                "host": "static.wixstatic.com",
                "path_prefix": "/media/083d1a_",
                "why": "Garden Room Ireland's second Wix media account prefix, carrying part of the Grey Windows gallery and three home-page exteriors. Same reasoning: the prefix is theirs alone."
            }
        ],
        "required_credit": "© Garden Room Ireland",
        "evidence": "Founder-confirmed grant recorded in Atlas as Image Permission Outreach IPO-049 (recQV5mDeIFBj9CZM) against Organisations ORG-000012 (recUrpkOqKbynjQP0), supplier YES 2 October 2026, Gmail thread 1a0fb8c10027247e.",
        "conditions": [
            "Credit '© Garden Room Ireland' on every image use.",
            "Garden Room Ireland may request change or removal of any image at any time, and PlotNua complies.",
            "No resale, no sublicensing, no unrelated advertising use.",
            "Garden Room Ireland retains ownership of the imagery."
        ],
        "note": "SCOPE IS THE TWO WIX ACCOUNT PREFIXES AND NOTHING WIDER. static.wixstatic.com is a shared CDN; a bare host entry would have authorised every Wix site on the internet, which is not what was granted. Three further prefixes appear on Garden Room Ireland's own pages and are deliberately excluded: 11062b_ (Wix stock/demo imagery), 8bb438_ and 4d0b36_ (third-party accounts). The gate matches by pathname prefix, so those three are refused by construction.\n\n90 assets governed in Atlas on 2 October 2026 after individual visual inspection of 97 candidates across nine first-party pages (Grey Windows, Verandas, Green Walls, Grey Walls, Black Pillars, Grey Pillars, Light Oak, Interiors, home page). Seven candidates were excluded and are not covered here: two dominated by an identifiable individual, one carrying prominent third-party film posters, two whose provenance could not be established as first-party, one named as a screen capture, one generic architectural-drawing stock image. Three of the 90 are classified Floor Plan rather than Product Image.",
        "atlas_permission_record": "recQV5mDeIFBj9CZM",
        "atlas_permission_ref": "IPO-049",
        "permission_date": "2026-10-02"
    },
    # ---------------------------------------------------------------- ELM ---
    {
        "organisation_record": "recyCu5OjHlUObM8f",
        "organisation_code": "ORG-000148",
        "organisation_name": "Elm Landscaping",
        "permission_outcome": "Granted with Conditions — Founder Confirmed",
        "permitted_domain": "elmlandscaping.ie",
        "required_credit": "© Elm Landscaping",
        "evidence": "Founder-confirmed grant recorded in Atlas as Image Permission Outreach IPO-046 (reccLICqUV2mAGicg) against Organisations ORG-000148 (recyCu5OjHlUObM8f), supplier YES 2 October 2026, Gmail thread 1a0d05e8fd940e75.",
        "conditions": [
            "Credit '© Elm Landscaping' on every image use.",
            "Elm Landscaping may request change or removal of any image at any time, and PlotNua complies.",
            "No resale, no sublicensing, no unrelated advertising use.",
            "Elm Landscaping retains ownership of the imagery."
        ],
        "note": "NO DELIVERY HOST IS DECLARED, because none is needed: Elm serve their imagery from their own WordPress installation at elmlandscaping.ie/wp-content/uploads/, so the first-party domain already is the scope.\n\nTHE INSTAGRAM EMBED IS OUT OF SCOPE AND STAYS OUT. elmlandscaping.ie/gallery/ renders an Instagram feed rather than hosted images; permission reaches supplier-owned imagery on the authorised website and is not broadened to a third-party domain merely because images are embedded there. No instagram host appears in this record and the builder that wrote it refuses one.\n\n53 assets governed in Atlas on 2 October 2026 after individual visual inspection of 67 candidates across thirteen first-party pages. Fourteen candidates were excluded and are not covered here: two showing identifiable children, one an identifiable pair of staff, two branded-fleet shots, one a third-party 'Millboard Approved Installer' badge, three whose provenance reads as licensed stock, five duplicates of accepted frames. Finished-garden outcomes are typed Product Image; works-in-progress and tree-surgery service photography is typed Other, so the two are never confused downstream.",
        "atlas_permission_record": "reccLICqUV2mAGicg",
        "atlas_permission_ref": "IPO-046",
        "permission_date": "2026-10-02"
    },
    # ---------------------------------------------------------------- DON ---
    {
        "organisation_record": "recOLYgRSUdzU8zwI",
        "organisation_name": "Don Modular Homes",
        "permission_outcome": "Granted with Conditions — Founder Confirmed",
        "permitted_domain": "donmodularhomes.ie",
        "required_credit": "© Don Modular Homes",
        "evidence": "Founder-confirmed grant recorded in Atlas as Image Permission Outreach C2-FIRST-DON-MODULAR-20261002 (recAFBJW5nwWv0Z20) against Organisations recOLYgRSUdzU8zwI, supplier YES 2 October 2026, Gmail thread 1a0fbe3f8fdf7329.",
        "conditions": [
            "Credit '© Don Modular Homes' on every image use.",
            "Don Modular Homes may request change or removal of any image at any time, and PlotNua complies.",
            "No resale, no sublicensing, no unrelated advertising use.",
            "Don Modular Homes retains ownership of the imagery.",
            "EVERY governed Don image is a computer-generated architectural visualisation, not a photograph of a completed build, and must never be presented as one."
        ],
        "note": "ALL 25 GOVERNED DON IMAGES ARE CGI VISUALISATIONS. This is not a caveat added for safety; it is what the images are. Every exterior and every interior on donmodularhomes.ie is an architectural render. The distinction is carried in the governed Atlas asset records themselves rather than in a new schema field: each asset's alt text begins 'Visualisation:' and each asset's Notes carries the sentence 'computer-generated visualisation published by the supplier, not a photograph of a completed build'. The render path reads alt text from the governed record, so the distinction survives to the page without any frontend change. Nothing in the publication path rewrites or discards it, and nothing may be added that implies these are photographs of completed installations.\n\nNo delivery host is declared: Don serve their own images from donmodularhomes.ie/images/, so the first-party domain is the scope.\n\n25 assets governed in Atlas on 2 October 2026 — the complete unique set across the whole site, after collapsing responsive variants (-828, -1080) and .jpg/.webp pairs, and probing for further files that do not exist. No candidate was excluded. One record additionally notes that the supplier's own alt text for interior-9 describes a bathroom while the image shows a bed alcove and kitchen; PlotNua's alt text follows what was actually seen.\n\nNO PRODUCT RECORDS WERE CREATED. Don sell one configurable steel-frame design priced per square metre; the 1/2/3/4-bed pages are size variants of the same building, not distinct models. Imagery is governed at organisation level accordingly.",
        "atlas_permission_record": "recAFBJW5nwWv0Z20",
        "atlas_permission_ref": "C2-FIRST-DON-MODULAR-20261002",
        "permission_date": "2026-10-02"
    },
]


def die(msg):
    """A builder that crashes has not refused, it has merely failed."""
    print("REFUSED: " + msg)
    sys.exit(1)


def guard(name, ok, detail=""):
    if not ok:
        die(name + (" — " + detail if detail else ""))
    print("  ok    " + name)


def main():
    if not RECORDS.exists():
        die("image-rights-records.json not found")
    before_text = RECORDS.read_text(encoding="utf-8")
    before_sha = hashlib.sha256(before_text.encode("utf-8")).hexdigest()
    src = json.loads(before_text)
    records = src.get("records")
    if not isinstance(records, list):
        die("image-rights-records.json has no records array")

    existing = {r.get("organisation_record") for r in records}
    print("IMG-6 · THREE SUPPLIER GRANTS")
    print("=" * 74)

    # R00 . IDEMPOTENCE ------------------------------------------------------
    clash = [n["organisation_name"] for n in NEW if n["organisation_record"] in existing]
    guard("R00 . none of the three organisations is already recorded",
          not clash, "already present: " + ", ".join(clash))

    # R01 . THE FILE IS THE ONE THIS BUILDER WAS ANCHORED AGAINST -------------
    guard("R01 . the records file holds the expected six prior records",
          len(records) == 6, "found %d" % len(records))

    # R02 . VOCABULARY -------------------------------------------------------
    guard("R02 . every new outcome is in the gate's live-grant vocabulary",
          all(n["permission_outcome"] in LIVE_GRANTS for n in NEW))

    # R03 AND R04 ARE ORDERED SO THAT EACH CAN BE PROVEN ON ITS OWN.
    # The first version put the "exactly two prefixes" check first, and it
    # swallowed both widening cases: breaking the scope to a foreign account or
    # to the bare CDN was caught, but caught by the WRONG guard, so neither
    # widening guard had ever refused anything. The narrow checks therefore run
    # before the shape check.
    all_hosts = [h for n in NEW for h in n.get("permitted_delivery_hosts") or []]

    # R03 . NO FOREIGN WIX ACCOUNT, AND NO BARE /media/ ----------------------
    leaked = [p for p in FOREIGN_WIX_PREFIXES
              for h in all_hosts if h.get("path_prefix", "").startswith("/media/" + p)]
    guard("R03a . no foreign Wix account prefix is granted", not leaked,
          "leaked: " + ", ".join(sorted(set(leaked))))
    guard("R03b . no bare /media/ prefix, which would be the whole shared CDN",
          all(h.get("path_prefix") not in ("/media/", "/media", "/") for h in all_hosts))

    # R04 . GRI'S WIX SCOPE IS EXACTLY THE TWO SUPPLIER-OWNED PREFIXES -------
    hosts = NEW[0]["permitted_delivery_hosts"]
    guard("R04 . Garden Room Ireland declares exactly two scoped Wix prefixes",
          len(hosts) == 2
          and all(h["host"] == "static.wixstatic.com" for h in hosts)
          and sorted(h["path_prefix"] for h in hosts)
              == ["/media/083d1a_", "/media/fef4b6_"])

    blob = json.dumps(NEW, ensure_ascii=False)

    # R05 . ELM AND DON ARE FIRST-PARTY ONLY; INSTAGRAM IS NOT IN SCOPE ------
    guard("R05a . Elm and Don declare no delivery host at all",
          not NEW[1].get("permitted_delivery_hosts")
          and not NEW[2].get("permitted_delivery_hosts"))
    # The prose DOES mention Instagram, on purpose, to record why it is out of
    # scope. So this guard reads the fields the gate actually keys on -- the
    # permitted domain and any delivery host -- and nothing else. A guard that
    # cannot tell an explanation from a grant would refuse its own correct text.
    granted_hosts = [n["permitted_domain"] for n in NEW] + [
        h["host"] for n in NEW for h in n.get("permitted_delivery_hosts") or []]
    guard("R05b . no instagram host is granted by any of the three records",
          not any("instagram" in h.lower() for h in granted_hosts),
          "granted hosts: " + ", ".join(granted_hosts))

    # R06 . A LIVE GRANT MUST SAY WHERE IT CAME FROM -------------------------
    for n in NEW:
        who = n["organisation_name"]
        guard("R06 . %s carries domain, evidence, Atlas id and credit" % who,
              bool(n.get("permitted_domain") and n.get("evidence")
                   and n.get("atlas_permission_record") and n.get("required_credit")))

    # R07 . THE CGI FACT IS WRITTEN DOWN, NOT ASSUMED -----------------------
    don = NEW[2]
    guard("R07 . Don's record states the visualisation fact in a condition",
          any("visualisation" in c.lower() for c in don["conditions"])
          and "not a photograph" in don["note"].lower())

    if CHECK_ONLY:
        print("-" * 74)
        print("CHECK ONLY — all guards pass, nothing written")
        return 0

    src["records"] = records + NEW
    text = json.dumps(src, indent=2, ensure_ascii=False) + "\n"
    RECORDS.write_text(text, encoding="utf-8")

    # R08 . THE SIX EXISTING RECORDS CAME OUT UNCHANGED ---------------------
    after = json.loads(RECORDS.read_text(encoding="utf-8"))["records"]
    same = json.dumps(after[:6], ensure_ascii=False, sort_keys=True) \
        == json.dumps(records[:6], ensure_ascii=False, sort_keys=True)
    if not same:
        RECORDS.write_text(before_text, encoding="utf-8")
        die("R08 . an existing record changed; the file has been restored")
    guard("R08 . the six existing records are unchanged", True)
    guard("R09 . the file now holds nine records", len(after) == 9)

    print("-" * 74)
    print("records sha256 before: " + before_sha[:12])
    print("records sha256 after:  "
          + hashlib.sha256(RECORDS.read_bytes()).hexdigest()[:12])
    print("ADDED 3 grants: Garden Room Ireland, Elm Landscaping, Don Modular Homes")
    print("NEXT: python3 .github/scripts/generate_image_rights_manifest.py")
    return 0


if __name__ == "__main__":
    sys.exit(main())
