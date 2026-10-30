#!/usr/bin/env python3
"""
BOUNDED BUILDER - DISC-008 SUPPLIER GALLERY: RIGHTS-RECORD NORMALISATION
=======================================================================
Founder approval, 30 Oct 2026: "The permissions verification dated 30 October
2026 is approved. ... Normalise the three approved supplier permission records
without expanding their original scope. Preserve all original evidence and
notes. Resolve the Yard Box / Yardbox naming difference without renaming the
supplier."

Touches exactly three rows of image-rights-records.json - ÖÖD House, Powersheds
and Yard Box - and regenerates image-rights-manifest.json from it. NO AIRTABLE
WRITE. NO SUPPLIER CONTACT. Every existing key, value, evidence string and note
is left byte-for-byte as it was; this script only APPENDS keys a row does not
yet have, and refuses to run if any of them is already present with a different
value.

What is added, and why it does not widen anything
-------------------------------------------------
* `approved_assets` - EXACTLY the images these three suppliers already have on a
  public PlotNua page: the Living in the Garden Maker Explorer
  (discovery-living-in-the-garden.html), live since the founder-approved
  Authorised Imagery Integration of 16 Oct 2026 (15b145e), each one already
  proven by the existing path (Atlas asset Supplier Provided + Approved, linked
  to its product, live manifest grant, scoped URL prefix, required credit). The
  list is read from the live page, not typed. Enumeration NARROWS what the
  gallery may use; it grants nothing new.
* `asset_approval_state` / `asset_approval` - says the above in the structured
  shape the gallery builder and its guards read.
* `permission` / `listing_review` / `public_visibility` / `hold_reason` (Powersheds
  and Yard Box only; ÖÖD already has them) - the facts already recorded in each
  row's evidence and in the supplier's own emails, in the shape the publication
  gate reads. Each quotation below was re-read in Gmail on 30 Oct 2026.
* `credit_href` (Powersheds, Yard Box) - where the required credit links. A link
  back to the supplier is not an image use and widens no scope.
* `maker_name_aliases` (Yard Box) - the explorer lists the maker as "Yardbox",
  the supplier's own spelling on its site and in Atlas. The record keeps its
  organisation_name "Yard Box" and its credit "Image: Yard Box" unchanged.

The medium is recorded per asset. The two Powersheds images are labelled
"Photograph" on the live explorer; one file is named by Powersheds itself
"..._CGI_LIFESTYLE_IMAGES_..." and both have the look of rendered scenes, so both
are recorded here as visualisations and the gallery labels them so. Founder
decision, 30 Oct 2026: the same classification applies on Results and in the
Maker Explorer (their alt text now begins "Visualisation:").

Usage:
  python3 atlas-tools/build-disc008-gallery-records.py           apply (idempotent)
  python3 atlas-tools/build-disc008-gallery-records.py --check   verify, write nothing
"""
import json, re, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RECORDS = ROOT / "image-rights-records.json"
PAGE = ROOT / "discovery-living-in-the-garden.html"
UNIVERSE = ROOT / "garden-room-recommendation-universe-v1.json"
MANIFEST_GEN = ROOT / ".github" / "scripts" / "generate_image_rights_manifest.py"

APPROVAL = ("founder approval 30 Oct 2026 (DISC-008 supplier gallery; permissions verification of "
            "30 Oct 2026 approved: use only images already authorised and published on PlotNua)")

# Per-asset medium where it differs from the live explorer label (see docstring).
VISUALISATION = {
    "https://cdn.shopify.com/s/files/1/0601/8967/1489/files/POW01001_CGI_LIFESTYLE_IMAGES_MAY24_SC03_LOGCABIN_S02_ADOBE_98.jpg":
        "Supplier's own filename names it CGI (\"..._CGI_LIFESTYLE_IMAGES_...\").",
    "https://cdn.shopify.com/s/files/1/0601/8967/1489/files/1610PALCTIMWDDW_d5c78ede-b4ff-441b-926e-8198c72f4ce4.png":
        "A rendered scene (uniform synthetic lighting and planting, 3200 x 3200 product render); the filename does not say. "
        "Classified as a visualisation by founder decision, 30 Oct 2026.",
}

ADD = {
    "ÖÖD House": {
        "explorer_maker": "ÖÖD House",
        "fields": {},          # permission / listing_review / public_visibility already present
        "authorised_by": "ÖÖD House, 14 Oct 2026 (Gertrud Ots, Head of Marketing, Gmail 1a139105565814d0: Drive photo library by product)",
        "conditions": ["Credit: ÖÖD House (and the named photographer where the file names one)",
                       "A working link to https://www.oodhouse.com/",
                       "Each image used only for the model named by ÖÖD's own folder",
                       "Hot-linked unmodified from ÖÖD's own Drive files; never downloaded, rehosted, cropped or altered",
                       "No implied endorsement, recommendation or residential suitability"],
    },
    "Powersheds": {
        "explorer_maker": "Powersheds",
        "fields": {
            "permission": {
                "state": "GRANTED",
                "ref": "IPO-POWERSHEDS-0001",
                "record": "reczCyWXPWvoA27GX",
                "date": "2026-09-28",
                "scope": ["feature", "imagery"],
                "conditions": ["credit", "removal-or-change-on-request", "selected-first-party-imagery-only", "unmodified-hotlink"],
                "asked": "PlotNua, 22 Sep 2026 (Gmail 1a0c9134d7ec505d), listing what an initial pilot would need: \"permission to use an agreed selection of Power Sheds product imagery\".",
                "answered": "\"I'm would be happy for you to use selected imagery from our website, provided it is clearly attributed to Powersheds. We'd just want to retain the right to ask for imagery to be removed or changed at any point if we felt it was no longer appropriate or the partnership wasn't working for us.\" (Jack Sutcliffe, 28 Sep 2026, Gmail 1a0e6e3dd5e73483)",
                "note": "Structured restatement, 30 Oct 2026, of the grant recorded above; nothing new is granted. 'feature' is the scope already recorded in Atlas IPO-POWERSHEDS-0001 (\"used when featuring Power Sheds on PlotNua\") and is confirmed by Jack's approval of the feature preview on 7 Oct. Jack's other points in the same email (pricing source, customer handover, attribution, no PlotNua discount) are commercial and are not image-rights scope."
            },
            "listing_review": {
                "state": "CONFIRMED",
                "requested_by": "plotnua",
                "requested_in": "Gmail 1a0e7d28cab8793f, 28 Sep 2026 (private preview sent: powersheds-preview.html)",
                "confirmed_at": "2026-10-07",
                "confirmed_in": "Gmail 1a116d6ba3130623",
                "note": "\"Seems ok to me - can you just change Power Sheds to Powersheds?\" - Jack Sutcliffe on the private preview, 7 Oct 2026. The name correction was applied on 8 Oct (see note above)."
            },
            "public_visibility": "PUBLISHABLE",
            "hold_reason": None,
            "credit_href": "https://ie.powersheds.com/",
        },
        "authorised_by": "Powersheds, 28 Sep 2026 (Jack Sutcliffe, Gmail 1a0e6e3dd5e73483; preview approved 7 Oct 2026, Gmail 1a116d6ba3130623)",
        "conditions": ["Credit: Image: Powersheds", "A working link to https://ie.powersheds.com/ (Powersheds' stated source of truth for Ireland)",
                       "Removed or changed whenever Powersheds asks",
                       "Hot-linked unmodified from Powersheds' own Shopify namespace; never downloaded, rehosted, cropped or altered",
                       "Rendered images are labelled Visualisation"],
    },
    "Yard Box": {
        "explorer_maker": "Yardbox",
        "fields": {
            "permission": {
                "state": "GRANTED",
                "ref": "IPO-032",
                "record": "recAWWIwLpJX8mAiW",
                "date": "2026-09-29",
                "scope": ["feature", "imagery"],
                "conditions": ["credit", "referenced-from-own-site-never-copied", "selected-first-party-imagery-only"],
                "asked": "\"Would you be happy for PlotNua to feature your company and use selected imagery from your website alongside the information about your products?\" (PlotNua, 24 Sep 2026, thread 1a0d05e09446b7fe; the imagery ask repeated 28 Sep)",
                "answered": "\"Imagery is ok to use.\" (Cormac Carville, Yard Box, 29 Sep 2026, Gmail 1a0ed8a508425026)",
                "note": "Structured restatement, 30 Oct 2026, of the grant recorded above; nothing new is granted. The two factual corrections in the same reply (Bothán footprint basis, design and manufacture credit) concern the Bothán and are recorded in bothan_attribution; the Bothán is not listed on DISC-008."
            },
            "listing_review": {
                "state": "NOT_REQUIRED",
                "requested_by": None,
                "requested_in": None,
                "note": "Yard Box did not ask to review a listing. PlotNua sent a private preview (yardbox-preview.html, 23 and 24 Sep 2026); Cormac's reply of 29 Sep granted imagery and corrected two Bothán facts. Founder decision 30 Oct 2026 (approval of the DISC-008 permissions verification): Yardbox may be featured without further contact."
            },
            "public_visibility": "PUBLISHABLE",
            "hold_reason": None,
            "credit_href": "https://www.yardbox.co.uk/",
            "maker_name_aliases": ["Yardbox"],
        },
        "authorised_by": "Yard Box, 29 Sep 2026 (Cormac Carville, Gmail 1a0ed8a508425026)",
        "conditions": ["Credit: Image: Yard Box", "A working link to https://www.yardbox.co.uk/",
                       "Referenced from Yard Box's own Squarespace namespace; never copied, rehosted, cropped or altered"],
    },
}


def live_images(maker):
    s = PAGE.read_text(encoding="utf-8")
    cfg = json.loads(re.search(r'id="mx-data">(.*?)</script>', s, re.S).group(1))
    out, lead = [], None
    for t in cfg["tabs"]:
        for m in t["makers"]:
            if m["m"] != maker:
                continue
            lead = (m.get("l") or {}).get("src")
            for p in m["p"]:
                if len(p) > 5 and isinstance(p[5], dict):
                    for im in p[5].get("img") or []:
                        out.append((p[0], p[1], im))
    return out, lead


def universe_index():
    idx = {}
    for x in json.loads(UNIVERSE.read_text(encoding="utf-8"))["products"]:
        for im in (x.get("imagerySet") or ([x["imagery"]] if x.get("imagery") else [])):
            idx.setdefault(im["url"], (x.get("productCode"), im.get("assetRecord")))
    return idx


def assets_for(maker):
    imgs, lead = live_images(maker)
    if not imgs:
        sys.exit(f"FAIL: no live DISC-008 images for {maker}")
    uni, seen, out = universe_index(), set(), []
    for pid, pname, im in imgs:
        u = im["src"]
        if u in seen:
            continue
        seen.add(u)
        if u not in uni:
            sys.exit(f"FAIL: {maker}: live image is not in the governed universe imagery: {u}")
        code, asset = uni[u]
        kind = "visualisation" if (u in VISUALISATION or im.get("kind", "").lower() == "visualisation") else "photograph"
        a = {"url": u, "product_code": code, "product_name": pname, "atlas_asset": asset, "kind": kind,
             "primary": u == lead, "alt": im["alt"]}
        if u in VISUALISATION:
            a["medium_note"] = (VISUALISATION[u] + " Founder confirmed the classification on 30 Oct 2026 (DISC-008 final release "
                                "preparation); Results and the Maker Explorer carry the same label via the asset's alt text "
                                "(.github/scripts/apply_authorised_imagery.py).")
        out.append(a)
    return out


def build(doc):
    for r in doc["records"]:
        spec = ADD.get(r["organisation_name"])
        if not spec:
            continue
        assets = assets_for(spec["explorer_maker"])
        add = dict(spec["fields"])
        add["asset_approval_state"] = "APPROVED"
        add["asset_approval"] = {
            "state": "SELECTED_ASSETS_APPROVED",
            "default_for_unlisted": "NOT_AUTHORISED",
            "approved_count": len(assets),
            "authorised_by": f"{spec['authorised_by']}; {APPROVAL}",
            "note": (f"Approval is by ENUMERATION, per asset. Listed: exactly the {len(assets)} image(s) this supplier already has on "
                     "discovery-living-in-the-garden.html (Maker Explorer, live since 16 Oct 2026, 15b145e), each already proven by "
                     "apply_authorised_imagery.py against this grant. This restates, and does not widen, the scope recorded above; "
                     "no other image is authorised by this list."),
            "conditions_on_every_use": spec["conditions"],
        }
        add["approved_assets"] = assets
        for k, v in add.items():
            if k in r and r[k] != v:
                sys.exit(f"FAIL: {r['organisation_name']}: '{k}' already present with a different value; refusing to overwrite")
            r[k] = v
    return doc


def dump(doc):
    return json.dumps(doc, indent=2, ensure_ascii=False) + "\n"


def main():
    raw = RECORDS.read_text(encoding="utf-8")
    before = json.loads(raw)
    keep = {r["organisation_name"]: dict(r) for r in before["records"]}
    after = build(json.loads(raw))
    # nothing pre-existing may change, on any row
    for r in after["records"]:
        old = keep[r["organisation_name"]]
        for k, v in old.items():
            if r.get(k) != v:
                sys.exit(f"FAIL: {r['organisation_name']}: existing field '{k}' would change")
        if r["organisation_name"] not in ADD and r != old:
            sys.exit(f"FAIL: {r['organisation_name']} would change; only the three approved rows may")
    out = dump(after)
    if "--check" in sys.argv:
        ok = out == raw
        print("DISC-008 GALLERY RECORDS · CHECK OK — three rows normalised, nothing else changed" if ok
              else "FAIL: DISC-008 gallery records are not applied")
        sys.exit(0 if ok else 1)
    RECORDS.write_text(out, encoding="utf-8")
    subprocess.run([sys.executable, str(MANIFEST_GEN)], cwd=ROOT, check=True)
    for name in ADD:
        r = next(x for x in after["records"] if x["organisation_name"] == name)
        print(f"{name}: {len(r['approved_assets'])} approved asset(s); public_visibility {r.get('public_visibility')}")


if __name__ == "__main__":
    main()
