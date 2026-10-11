#!/usr/bin/env python3
"""
BOUNDED BUILDER — APPROVE SELECTED BIOBUILDS ASSETS FOR PUBLICATION
====================================================================
Five anchored edits to atlas-tools/build-publication-gate-records.py, so the
ONE writer of the BIOBUILDS rights record also carries the per-asset approval
the founder authorised on 11 October 2026.

PER ASSET, NOT PER ORGANISATION. The founder's instruction was explicit:
select suitable images, approve only those, and leave the rest REFERENCE_ONLY.
So `asset_approval_state` keeps its value as the DEFAULT FOR EVERY ASSET NOT
NAMED, and `approved_assets` is the enumerated exception list. Nothing is
approved by being on the domain; an asset is approved by being written down.

THE SELECTION. Eight of the 34 governed assets are exercised on the private
preview. Six depict the two products and are approved:

  WANDERLUST   wanderlust-catalog          exterior
               wanderlust-48-int-catalog   interior
               wanderlust-48-bedroom       interior
  SERENITY     serenity-catalog            exterior
               serenity-95-int-catalog     interior
               serenity-95-bathroom        interior

Two are NOT approved and stay REFERENCE_ONLY, because neither depicts a
product a homeowner is choosing between:

  wall-section-3.0         a construction detail of the wall build-up
  prefab-48-crane-lift     a process shot of a module being craned

Leaving them out is not caution for its own sake. The founder authorised
"selected" imagery, and a selection that quietly included everything would
not be a selection.

CONDITION 7 IS LOAD-BEARING, AND IT SURVIVES THIS CHANGE.

The grant records: "THE MEDIUM OF THE MODEL IMAGERY IS NOT ESTABLISHED.
BIOBUILDS has not said whether the model images on their site are photographs
of completed homes or architectural visualisations, and the question has been
put to them. Until they answer, no PlotNua surface may describe them as
either."

That is why the supplier's own caption -- "BIOBUILDS model imagery" -- is the
one used everywhere, and why no alt text written here contains the word
photograph, render, visualisation or photo. The founder's authorisation is a
decision about PUBLICATION. Condition 7 is a constraint on WORDING. Both hold
at once, and G5 below asserts the wording one.

WHAT ELSE IS PRESERVED EXACTLY. The supplier's words, the credit, the
link-back, the withdrawal right, ownership, the no-resale term, and
listing_review.state = AWAITING_CONFIRMATION with confirmed_at null. Mateus
has still not confirmed the corrected preview and this builder does not say
he has.

    python3 atlas-tools/build-biobuilds-asset-approval.py [--check] [--revert]

Exit 0 = applied, or already correct.
"""
import difflib
import pathlib
import shutil
import sys

HERE = pathlib.Path(__file__).resolve().parent
SRC = HERE / "build-publication-gate-records.py"
BAK = SRC.with_suffix(".py.bak2")

CHECK = "--check" in sys.argv
REVERT = "--revert" in sys.argv
SENTINEL = "APPROVED_ASSETS"

MEDIA = "https://www.biobuilds.com/_next/static/immutable/media/"


def die(msg):
    print("REFUSED: " + msg)
    sys.exit(1)


# ── 1 · the selection, as data ───────────────────────────────────────────
A1_OLD = '''def die(msg):
    print("REFUSED: " + msg)
    sys.exit(1)
'''

A1_NEW = '''# ── THE APPROVED ASSET SELECTION ─────────────────────────────────────────
#
# Founder authorisation, 11 October 2026, under
# FX-BIOBUILDS-PUBLISH-20261011: selected BIOBUILDS imagery may be published,
# within the scope of the written grant of 2 October 2026.
#
# APPROVAL IS BY ENUMERATION. An asset is publishable because it is in this
# list, never because it is on the supplier's domain. The two assets exercised
# on the preview that are NOT here -- wall-section-3.0 and
# prefab-48-crane-lift -- remain REFERENCE_ONLY, as do the other 26 governed
# assets.
#
# NO ALT TEXT HERE SAYS photograph, photo, render OR visualisation. Grant
# condition 7 records that BIOBUILDS has never said which the model imagery
# is, and that until they answer no PlotNua surface may describe it as either.
# The supplier's own caption is medium-neutral and is used verbatim.
MEDIA_PREFIX = "https://www.biobuilds.com/_next/static/immutable/media/"
SUPPLIER_CAPTION = "BIOBUILDS model imagery"
SUPPLIER_CREDIT = "\\u00a9 BIOBUILDS"
SUPPLIER_LINK = "https://www.biobuilds.com/"

APPROVED_ASSETS = [
    {
        "url": MEDIA_PREFIX + "wanderlust-catalog.3-furbv0o-vtc.jpg",
        "product_code": "PROD-000523",
        "product_name": "BIOBUILDS Wanderlust",
        "role": "exterior",
        "primary": True,
        "alt": "The BIOBUILDS Wanderlust 48 seen from outside, a timber-clad "
               "single-storey building with full-height glazing.",
    },
    {
        "url": MEDIA_PREFIX + "wanderlust-48-int-catalog.0d9n8s-fzmg7q.jpg",
        "product_code": "PROD-000523",
        "product_name": "BIOBUILDS Wanderlust",
        "role": "interior",
        "primary": False,
        "alt": "Inside the BIOBUILDS Wanderlust 48, an open living space with "
               "timber finishes and glazing to the garden.",
    },
    {
        "url": MEDIA_PREFIX + "wanderlust-48-bedroom.02gun-re0wb_5.jpg",
        "product_code": "PROD-000523",
        "product_name": "BIOBUILDS Wanderlust",
        "role": "interior",
        "primary": False,
        "alt": "A bedroom in the BIOBUILDS Wanderlust 48, with timber walls "
               "and a window to the garden.",
    },
    {
        "url": MEDIA_PREFIX + "serenity-catalog.2xcd8x45pacpa.jpg",
        "product_code": "PROD-000524",
        "product_name": "BIOBUILDS Serenity",
        "role": "exterior",
        "primary": True,
        "alt": "The BIOBUILDS Serenity 95 seen from outside, a larger "
               "timber-clad house with extensive glazing.",
    },
    {
        "url": MEDIA_PREFIX + "serenity-95-int-catalog.0uuneoqa7y-h8.jpg",
        "product_code": "PROD-000524",
        "product_name": "BIOBUILDS Serenity",
        "role": "interior",
        "primary": False,
        "alt": "Inside the BIOBUILDS Serenity 95, an open-plan living and "
               "dining space with timber finishes.",
    },
    {
        "url": MEDIA_PREFIX + "serenity-95-bathroom.1nmu58m7tl0_u.jpg",
        "product_code": "PROD-000524",
        "product_name": "BIOBUILDS Serenity",
        "role": "interior",
        "primary": False,
        "alt": "A bathroom in the BIOBUILDS Serenity 95, with tiled surfaces "
               "and fixed sanitaryware.",
    },
]

# Exercised on the private preview and DELIBERATELY NOT approved: neither
# depicts a product a homeowner is choosing between.
WITHHELD_ASSETS = [
    {"url": MEDIA_PREFIX + "wall-section-3.0.26fqr4wmqyq13.jpg",
     "reason": "a construction detail of the wall build-up, not a product"},
    {"url": MEDIA_PREFIX + "prefab-48-crane-lift.2fhf6txqe9e82.jpg",
     "reason": "a process shot of a module being craned, not a product"},
]

ASSET_APPROVAL = {
    "state": "SELECTED_ASSETS_APPROVED",
    "default_for_unlisted": "REFERENCE_ONLY",
    "approved_count": len(APPROVED_ASSETS),
    "withheld_on_preview": len(WITHHELD_ASSETS),
    "governed_total_in_atlas": 34,
    "authorised_by": "FX-BIOBUILDS-PUBLISH-20261011",
    "note": ("Approval is by ENUMERATION, per asset. An asset is publishable "
             "because it appears in approved_assets, never because it is "
             "served from the supplier's domain. Every asset not listed "
             "remains Reference Only - Not Published, including the two "
             "exercised on the private preview. The internal REFERENCE_ONLY "
             "state was never a refusal by BIOBUILDS; it was PlotNua's own "
             "publication restriction, and the founder has lifted it for the "
             "six selected assets only."),
    "conditions_on_every_use": [
        "Caption: " + SUPPLIER_CAPTION,
        "Credit: " + SUPPLIER_CREDIT,
        "A working link to " + SUPPLIER_LINK,
        "No PlotNua surface describes the medium: grant condition 7 stands "
        "until BIOBUILDS answers.",
        "No surface implies the imagery shows a completed installation in "
        "Ireland.",
    ],
}


def die(msg):
    print("REFUSED: " + msg)
    sys.exit(1)
'''

# ── 2 · the pre-live-review condition records the founder's decision ─────
A2_OLD = '''    "conditions": ["credit", "link-back", "pre-live-review",
                   "withdrawable-on-request"],
}'''

A2_NEW = '''    "conditions": ["credit", "link-back", "pre-live-review",
                   "withdrawable-on-request"],
    # The supplier's pre-live-review request is NOT removed and NOT satisfied.
    # It was asked for, it has not been answered, and the founder decided to
    # proceed anyway. All three facts are recorded; none is tidied away.
    "pre_live_review_disposition": {
        "requested_by_supplier": True,
        "answered_by_supplier": False,
        "proceeded_under": "FX-BIOBUILDS-PUBLISH-20261011",
        "note": ("BIOBUILDS asked to see the listing before it went live. The "
                 "corrections they requested on 11 October 2026 are "
                 "implemented. They have not confirmed the revised preview. "
                 "The founder decided to publish without that confirmation "
                 "and accepts responsibility for doing so. This supersedes "
                 "PlotNua's earlier reading that the grant covered the "
                 "private preview only -- that was PlotNua's own scoping of "
                 "its own restraint, not a limit BIOBUILDS placed on the "
                 "grant."),
    },
}'''

# ── 3 · what gets written onto the row ───────────────────────────────────
A3_OLD = '''        row["asset_approval_state"] = asset_state
        row["founder_exception"] = FOUNDER_EXCEPTION'''

A3_NEW = '''        row["asset_approval_state"] = asset_state
        row["asset_approval"] = ASSET_APPROVAL
        row["approved_assets"] = APPROVED_ASSETS
        row["withheld_assets"] = WITHHELD_ASSETS
        row["founder_exception"] = FOUNDER_EXCEPTION'''

# ── 4 · the exception's scope no longer excludes imagery ────────────────
A4_OLD = '''    "scope": (
        "Authorises PUBLICATION OF THE PRODUCT LISTING in public Results, "
        "Compare and search. Does NOT authorise publication of BIOBUILDS "
        "imagery on any public page: the imagery grant remains scoped by "
        "this record's own conditions to the private noindexed review "
        "preview, the public Additional Home payload carries no image block, "
        "and prove-biobuilds-containment.mjs continues to enforce it."
    ),'''

A4_NEW = '''    "scope": (
        "Authorises PUBLICATION OF THE PRODUCT LISTING in public Results and "
        "Compare, AND publication of the SIX ENUMERATED ASSETS in "
        "approved_assets, each with the supplier's caption, the credit and a "
        "working link back. WIDENED 11 October 2026 by the same founder "
        "decision: the earlier version of this scope excluded imagery "
        "entirely, because at that point no imagery had been authorised. It "
        "does NOT authorise any asset outside that list -- every other "
        "BIOBUILDS asset, including the two exercised on the private "
        "preview, remains Reference Only, and "
        "prove-biobuilds-containment.mjs enforces the difference per asset "
        "rather than per domain."
    ),'''

# ── 5 · the closing report tells the truth about imagery ────────────────
A5_OLD = '''    print("Imagery stays scoped to the private review preview.")'''

A5_NEW = '''    print("Imagery: %d asset(s) approved for publication, %d withheld on "
          "the preview," % (len(APPROVED_ASSETS), len(WITHHELD_ASSETS)))
    print("and every other governed BIOBUILDS asset remains Reference Only.")
    print("Grant condition 7 stands: no surface describes the medium.")'''

EDITS = [("the module preamble", A1_OLD, A1_NEW),
         ("the permission conditions", A2_OLD, A2_NEW),
         ("the row write", A3_OLD, A3_NEW),
         ("the exception scope", A4_OLD, A4_NEW),
         ("the closing report", A5_OLD, A5_NEW)]

# Words no alt text or caption may contain, because grant condition 7 says the
# medium is not established.
MEDIUM_WORDS = ("photograph", "photo ", "photos", "render", "rendering",
                "visualisation", "visualization", "cgi", "3d model")
# And nothing may claim an Irish installation.
PLACE_CLAIMS = ("installed in ireland", "in an irish garden",
                "completed in ireland", "built in ireland")


def main():
    if not SRC.exists():
        die("build-publication-gate-records.py is not where this builder "
            "expects it.")
    src = SRC.read_text(encoding="utf-8")

    if REVERT:
        if not BAK.exists():
            die("there is no .bak2 sidecar to revert to.")
        shutil.copyfile(BAK, SRC)
        print("REVERTED build-publication-gate-records.py.")
        return

    already = SENTINEL in src
    if already:
        out = src
    else:
        for name, old, _ in EDITS:
            n = src.count(old)
            if n != 1:
                die("%s was found %d times, not once. The gate-records "
                    "builder has moved. Nothing written." % (name, n))
        out = src
        for _, old, new in EDITS:
            out = out.replace(old, new, 1)
        back = out
        for _, old, new in reversed(EDITS):
            back = back.replace(new, old, 1)
        if back != src:
            die("reversing the five replacements did not reproduce the "
                "original file. Nothing written.")

    # G1 · SIX APPROVED, TWO WITHHELD, AND THE WITHHELD ARE NAMED.
    for u in ("wanderlust-catalog", "wanderlust-48-int-catalog",
              "wanderlust-48-bedroom", "serenity-catalog",
              "serenity-95-int-catalog", "serenity-95-bathroom"):
        if u not in out:
            die("the approved selection is missing %s. Nothing written." % u)
    for u in ("wall-section-3.0", "prefab-48-crane-lift"):
        if u not in out:
            die("the withheld list is missing %s. An asset that is neither "
                "approved nor explicitly withheld is an asset nobody "
                "decided about. Nothing written." % u)

    # G2 · EVERY APPROVED URL IS ON THE SUPPLIER'S OWN ORIGIN, under the one
    # narrow prefix. A grant to use a supplier's images is not a grant to use
    # anything reachable from their hostname.
    block = out[out.find("APPROVED_ASSETS = ["):]
    block = block[:block.find("\n]") + 2]
    if block.count("MEDIA_PREFIX + ") != 6:
        die("not every approved asset is built from the single permitted "
            "prefix. Nothing written.")

    # G3 · ONE PRIMARY PER PRODUCT. Two primaries would make the hero
    # arbitrary; none would leave it empty.
    if block.count('"primary": True') != 2:
        die("there must be exactly one primary image per product (found %d). "
            "Nothing written." % block.count('"primary": True'))

    # G4 · THE SUPPLIER'S OWN CAPTION, CREDIT AND LINK ARE CARRIED.
    for need in ("BIOBUILDS model imagery", "\\u00a9 BIOBUILDS",
                 "https://www.biobuilds.com/"):
        if need not in out:
            die("the grant condition %r is not carried. Nothing written."
                % need)

    # G5 · CONDITION 7. No alt text and no caption may say what the medium is.
    # This is the assertion that keeps the founder's publication decision and
    # the supplier's unanswered question from colliding.
    low = block.lower()
    for w in MEDIUM_WORDS:
        if w in low:
            die("an approved asset's alt text contains %r. Grant condition 7 "
                "says the medium is not established and no surface may "
                "describe it. Nothing written." % w.strip())

    # G6 · AND NOTHING CLAIMS AN IRISH INSTALLATION.
    for w in PLACE_CLAIMS:
        if w in low:
            die("an approved asset's alt text claims %r. Model imagery must "
                "not be presented as a completed Irish installation. Nothing "
                "written." % w)

    # G7 · THE SUPPLIER'S REVIEW REQUEST IS STILL RECORDED AS UNANSWERED.
    if ('"answered_by_supplier": False' not in out
            or '"requested_by_supplier": True' not in out):
        die("the pre-live-review disposition no longer records that the "
            "supplier asked and has not answered. Nothing written.")

    # G8 · AND THE REVIEW STATE IS STILL UNCONFIRMED.
    lr = out[out.find("LISTING_REVIEW = {"):]
    lr = lr[:lr.find("\n}") + 2]
    if ('"state": "AWAITING_CONFIRMATION"' not in lr
            or '"confirmed_at": None' not in lr):
        die("the listing review no longer records AWAITING_CONFIRMATION with "
            "confirmed_at None. Nothing written.")

    print("\nBIOBUILDS ASSET APPROVAL")
    print("=" * 74)
    if already:
        print("  ok    already in place; nothing to do")
    else:
        print("  ok    G0  all five anchors matched once; nothing else moved")
    print("  ok    G1  six assets approved by name, two withheld by name")
    print("  ok    G2  every approved URL is on the one permitted prefix")
    print("  ok    G3  exactly one primary image per product")
    print("  ok    G4  the caption, credit and link-back are carried")
    print("  ok    G5  no alt text describes the medium (grant condition 7)")
    print("  ok    G6  no alt text claims an Irish installation")
    print("  ok    G7  the supplier's review request is recorded as unanswered")
    print("  ok    G8  listing_review stays AWAITING_CONFIRMATION")

    if CHECK:
        print("-" * 74)
        print("CHECK ONLY. Nothing written.")
        if not already:
            print("\n".join(difflib.unified_diff(
                src.splitlines(), out.splitlines(),
                "build-publication-gate-records.py",
                "build-publication-gate-records.py (proposed)",
                lineterm="", n=1)))
        return
    if already:
        print("-" * 74)
        print("No change needed.")
        return

    if not BAK.exists():
        shutil.copyfile(SRC, BAK)
    SRC.write_text(out, encoding="utf-8")
    print("-" * 74)
    print("wrote %s (%d bytes)" % (SRC.name, len(out.encode("utf-8"))))
    print("Now run it:  python3 atlas-tools/build-publication-gate-records.py")


if __name__ == "__main__":
    main()
