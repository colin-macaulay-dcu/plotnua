#!/usr/bin/env python3
"""
POWERSHEDS · SUPPLIER NAME CORRECTION — "Power Sheds" -> "Powersheds"
===============================================================================
AUTHORITY. Email from Jack Sutcliffe, Powersheds, 8 October 2026, verbatim:
"Hello / Seems ok to me - can you just change Power Sheds to Powersheds? /
Cheers / Jack Sutcliffe". Two separate things: approval of the feature as
shown, and an explicit correction of his own company name. Founder decisions of
8 October 2026: change the governed credit to "Image: Powersheds", and move the
credit, grant record, manifest, preview and universe TOGETHER.

CORROBORATION already held first-party: the registered entity is "Powersheds
Limited, UK company number 11790351" and the 13 linked Atlas Source records
were already titled "Powersheds — …". The closed form is the company's own
name; "Power Sheds" was PlotNua's rendering of it.

WHY THIS IS ONE ATOMIC BUILDER AND NOT A SEQUENCE OF EDITS.
validate-image-rights.js refuses a published image whose `required_credit` is
not present in the page text. The credit therefore lives in SEVEN coupled
places, and any partial change breaks the gate in one direction or the other:
the grant record, the generated manifest, the preview page (x2 credit lines),
the recommendation universe (x3 per-product credits), the certified supplier
module, and the /go pilot module. They move in one pass or not at all.

WHAT THIS DOES NOT TOUCH — and the reason, in each case:

  * HISTORICAL GOVERNANCE AND COMMERCIAL RECORDS. 09 Commercial/POWER-SHEDS-*,
    every atlas-*-report.md, the PHASE-6* write ledgers and release-diff
    records. These record the state and the wording in force at the time. A
    global replace would falsify them.
  * THE PERMISSION EVIDENCE SENTENCE. "Granted by Jack Sutcliffe of Power
    Sheds BY EMAIL, Gmail thread 1a0b5d1a7cf5e664 … IPO-POWERSHEDS-0001" is
    preserved VERBATIM. It is the record of what was granted, by whom, under
    what name, on 28 September. The correction is APPENDED beside it.
  * THE ORG-ID-CORRECTION NOTE. Also preserved verbatim, for the same reason:
    it documents a real earlier mistake and its repair.
  * shadow-budget-v2/phase5, phase6b, phase6d AND the phase ledgers. Those are
    dated phase artefacts and derived snapshots, not live data. The live
    artefacts are the four at repository root.
  * ATLAS RANKING, qualification, price governance, evidence rules, image-rights
    GATE LOGIC, and every other supplier. Guards below assert each of these.
  * The 158 Atlas Asset titles and 40 product names — founder instruction, and
    no homeowner sees them.

    python3 build-powersheds-name-correction.py --check   # guards only
    python3 build-powersheds-name-correction.py           # apply
"""

import hashlib
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
LIVE = ROOT.parent.parent / "03 Website" / "Live Website"
INFRA = ROOT.parent / "plotnua-infrastructure"

OLD, NEW = "Power Sheds", "Powersheds"
OLD_CREDIT, NEW_CREDIT = "Image: Power Sheds", "Image: Powersheds"

# Preserved VERBATIM. If any of these strings stops appearing exactly once in
# the file that holds it, the builder refuses: the historical record is the
# thing most easily destroyed by a rename, so it is guarded hardest.
EVIDENCE_SENTENCE = (
    "Granted by Jack Sutcliffe of Power Sheds BY EMAIL, Gmail thread "
    "1a0b5d1a7cf5e664, recorded in Atlas 28 September 2026 as Image Permission "
    "Outreach IPO-POWERSHEDS-0001 (reczCyWXPWvoA27GX)")
ORG_ID_NOTE_OPENING = (
    "ORGANISATION ID CORRECTED BEFORE PUSH. This record was first written with "
    "ORG-000194, which is Nua Modular (recuvqPv7XW0b0PFJ), not Power Sheds.")

CORRECTION_NOTE = (
    "\n\nSUPPLIER NAME CORRECTED 2026-10-08. Jack Sutcliffe of Powersheds "
    "wrote: \"Seems ok to me - can you just change Power Sheds to "
    "Powersheds?\". That email is two things: his approval of the feature as "
    "shown to him, and an explicit correction of his own company name. It is "
    "NOT a new or wider grant — the grant is still exactly "
    "IPO-POWERSHEDS-0001 of 28 September 2026 and its scope is unchanged. "
    "Under founder decision of 2026-10-08 the required credit moved from "
    "'Image: Power Sheds' to 'Image: Powersheds', and the credit, this record, "
    "the generated manifest, powersheds-preview.html and the recommendation "
    "universe were changed in ONE atomic pass, because the gate refuses any "
    "image whose required credit is absent from the page and they cannot be "
    "allowed to drift apart. The evidence sentence above and the "
    "ORGANISATION ID note below are preserved verbatim: they record the state "
    "and the wording in force at the time, and are not rewritten. "
    "Corroboration already held: the registered entity is 'Powersheds "
    "Limited, UK company number 11790351'.")

# ---------------------------------------------------------------- live targets
ROOT_JSON = ["atlas-recognition-pool.json",
             "garden-room-recommendation-universe-v1.json",
             "garden-room-detail-suppliers-v1.json",
             "image-rights-records.json",
             "image-rights-manifest.json"]
PAGE = "powersheds-preview.html"
IMAGERY = ".github/scripts/apply_authorised_imagery.py"
MODULE = LIVE / "supplier-previews-build" / "supplier_powersheds.py"
GO_MANIFEST = INFRA / "supplier-outreach" / "powersheds" / "powersheds-manifest.json"
GO_MODULE = INFRA / "supplier-outreach" / "powersheds" / "powersheds-module.html"
GO_GUARD = INFRA / "supplier-outreach" / "powersheds" / "prove-powersheds-guards.py"

BASE_SHA = {
    "atlas-recognition-pool.json": "1fc90f3cfb6942d5",
    "garden-room-recommendation-universe-v1.json": "470cb6238e8c6dd9",
    "garden-room-detail-suppliers-v1.json": "0bdc43f76e278381",
    "image-rights-records.json": "af1a126e05701e22",
    "image-rights-manifest.json": "1bb05cfa825e9a3f",
    "powersheds-preview.html": "80042c0e0a116d64",
    ".github/scripts/apply_authorised_imagery.py": "4212fd3119879ce2",
}

# Paths that must NOT change. Historical by nature.
MUST_NOT_CHANGE = [
    ROOT / "atlas-tools" / "shadow-budget-v2",
    ROOT.parent.parent / "09 Commercial",
]

def die(m):
    print("REFUSED: " + m)
    sys.exit(1)

def sha16(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()[:16]

def rename(text):
    """Replace the supplier name, credit included. Order matters: the credit is
    a superstring of the name, and replacing the name first would leave
    'Image: Powersheds' unreachable by the credit rule. Both end at the same
    string either way, but doing the credit first keeps the two rules
    independently countable, which the guards rely on."""
    return text.replace(OLD_CREDIT, NEW_CREDIT).replace(OLD, NEW)


def main():
    check = "--check" in sys.argv
    print("  POWERSHEDS NAME CORRECTION — Power Sheds -> Powersheds\n")

    # ---- guard 1 · every live target is the artefact measured at baseline
    for rel, want in BASE_SHA.items():
        got = sha16(ROOT / rel)
        if got != want:
            die("%s is %s..., baseline was %s... — refusing to patch an "
                "unexpected file" % (rel, got, want))
    print("  G1  all 7 live targets match the measured baseline        OK")

    for p in (MODULE, GO_MANIFEST, GO_MODULE, GO_GUARD):
        if not p.exists():
            die("missing coupled file: %s" % p)
    print("  G2  the 4 coupled off-repo files are present             OK")

    # ---- guard 3 · not re-runnable
    recs = (ROOT / "image-rights-records.json").read_text(encoding="utf-8")
    if NEW_CREDIT in recs:
        die("'%s' is already present in the grant record; this builder is not "
            "re-runnable over its own output" % NEW_CREDIT)
    print("  G3  not re-runnable over its own output                  OK")

    # ---- guard 4 · the historical record exists to be preserved
    if recs.count(EVIDENCE_SENTENCE) != 1:
        die("the IPO-POWERSHEDS-0001 evidence sentence is not present exactly "
            "once in image-rights-records.json before the patch")
    if recs.count(ORG_ID_NOTE_OPENING) != 1:
        die("the ORGANISATION ID note is not present exactly once before the "
            "patch")
    print("  G4  historical evidence present, ready to preserve        OK")

    # ------------------------------------------------------------ apply
    out = {}
    for rel in ROOT_JSON + [PAGE, IMAGERY]:
        src = (ROOT / rel).read_text(encoding="utf-8")
        out[rel] = rename(src)
    for p in (MODULE, GO_MANIFEST, GO_MODULE, GO_GUARD):
        out[str(p)] = rename(p.read_text(encoding="utf-8"))

    # The historical sentences are restored verbatim AFTER the rename, then the
    # dated correction is appended beside them. This is the whole point: the
    # rename is allowed to sweep the file, and the record of the past is put
    # back exactly as it was.
    for rel in ("image-rights-records.json", "image-rights-manifest.json"):
        t = out[rel]
        t = t.replace(json.dumps(rename(EVIDENCE_SENTENCE))[1:-1],
                      json.dumps(EVIDENCE_SENTENCE)[1:-1])
        t = t.replace(json.dumps(rename(ORG_ID_NOTE_OPENING))[1:-1],
                      json.dumps(ORG_ID_NOTE_OPENING)[1:-1])
        d = json.loads(t)
        rows = d["records"] if "records" in d else d["rows"]
        ps = [r for r in rows if r.get("organisation_record_id") == "recZyvRt8pDg5spUU"
              or r.get("organisation_name") == NEW]
        if len(ps) != 1:
            die("expected exactly one Powersheds row in %s, found %d" % (rel, len(ps)))
        ps[0]["note"] = ps[0]["note"] + CORRECTION_NOTE
        out[rel] = json.dumps(d, indent=2, ensure_ascii=False) + "\n"

    # ---- guard 5 · the historical record survived, verbatim
    for rel in ("image-rights-records.json", "image-rights-manifest.json"):
        if out[rel].count(EVIDENCE_SENTENCE) != 1:
            die("the IPO-POWERSHEDS-0001 evidence sentence did not survive "
                "verbatim in %s" % rel)
        if out[rel].count(ORG_ID_NOTE_OPENING) != 1:
            die("the ORGANISATION ID note did not survive verbatim in %s" % rel)
        if "SUPPLIER NAME CORRECTED 2026-10-08" not in out[rel]:
            die("the dated correction note was not appended in %s" % rel)
    print("  G5  evidence + ORG-ID note preserved VERBATIM, note added OK")

    # ---- guard 6 · the credit moved everywhere OPERATIVE, in lockstep.
    # ASSERTION, NOT MENTION. The preserved ORG-ID note QUOTES the old credit
    # ("carrying the credit 'Image: Power Sheds'") because that is what was in
    # force then. A first version of this guard searched the whole file and
    # fired on that quotation — it would have forced me either to falsify the
    # history or to drop the guard. The gate reads the `required_credit` FIELD
    # and the PAGE TEXT; a quotation inside a note is inert. So the guard checks
    # the operative surfaces precisely, and proves separately that every
    # surviving mention of the old name sits inside a note field.
    for rel in ("image-rights-records.json", "image-rights-manifest.json"):
        d = json.loads(out[rel])
        for r in (d["records"] if "records" in d else d["rows"]):
            if r.get("required_credit") == OLD_CREDIT:
                die("%s: required_credit is still %r — the gate would refuse "
                    "the image" % (rel, OLD_CREDIT))
            for c in r.get("conditions") or []:
                if OLD in c:
                    die("%s: a CONDITION still says %r: %r" % (rel, OLD, c))
            row = dict(r)
            row.pop("note", None)
            row.pop("evidence", None)
            if OLD in json.dumps(row, ensure_ascii=False):
                die("%s: %r survives OUTSIDE the note/evidence fields, which "
                    "are the only places history may be quoted" % (rel, OLD))
    print("      (old name quoted only inside preserved note/evidence — "
          "deliberate)")
    for rel in (PAGE, "atlas-recognition-pool.json",
                "garden-room-recommendation-universe-v1.json",
                "garden-room-detail-suppliers-v1.json", IMAGERY):
        if OLD in out[rel]:
            die("%r still present in %s, which carries no historical note"
                % (OLD, rel))
    for p2 in (MODULE, GO_MANIFEST, GO_MODULE, GO_GUARD):
        if OLD in out[str(p2)]:
            die("%r still present in %s" % (OLD, p2.name))
    page_credits = out[PAGE].count(NEW_CREDIT)
    if page_credits < 2:
        die("powersheds-preview.html carries %d corrected credit lines, "
            "expected at least 2" % page_credits)
    uni = json.loads(out["garden-room-recommendation-universe-v1.json"])
    uc = sum(1 for p in uni["products"]
             if (p.get("imagery") or {}).get("credit") == NEW_CREDIT)
    if uc != 3:
        die("expected 3 corrected per-product credits in the universe, got %d" % uc)
    print("  G6  credit moved in lockstep: page %d, universe %d          OK"
          % (page_credits, uc))

    # ---- guard 7 · the name moved on every homeowner-visible surface
    pool = json.loads(out["atlas-recognition-pool.json"])
    pn = sum(1 for e in pool if e.get("organisation") == NEW)
    po = sum(1 for e in pool if e.get("organisation") == OLD)
    if pn != 40 or po != 0:
        die("recognition pool: expected 40 'Powersheds' and 0 'Power Sheds', "
            "got %d and %d" % (pn, po))
    un = sum(1 for p in uni["products"] if p.get("organisation") == NEW)
    uo = sum(1 for p in uni["products"] if p.get("organisation") == OLD)
    if un != 3 or uo != 0:
        die("universe: expected 3 'Powersheds' and 0 'Power Sheds', got %d and %d"
            % (un, uo))
    alts = [(p.get("imagery") or {}).get("alt", "") for p in uni["products"]
            if p.get("organisation") == NEW]
    if any(OLD in a for a in alts):
        die("universe imagery alt text still says 'Power Sheds': %s" % alts)
    print("  G7  name corrected: pool 40/40, universe 3/3, alt text     OK")

    # ---- guard 8 · RANKING AND PRICE GOVERNANCE UNTOUCHED.
    # Every field that feeds matching is compared value-for-value against the
    # baseline. This is the guard that matters most: a rename must not move a
    # single price, tier, qualification or evidence state.
    before = json.loads((ROOT / "garden-room-recommendation-universe-v1.json")
                        .read_text(encoding="utf-8"))
    MATCH_FIELDS = ("price", "priceBasis", "priceBasisClass", "priceStatus",
                    "priceType", "priceScope", "priceSafeForMatching",
                    "priceEvidenceState", "priceIsRangeFloor", "vatRate",
                    "vatStatus", "qualification", "qualificationTier",
                    "qualificationCaveats", "verificationStatus",
                    "availabilityStatus", "irishAvailability",
                    "noPublishedIrishRoute", "floorAreaM2", "designLanguage",
                    "insulation", "glazing", "features")
    if len(before["products"]) != len(uni["products"]):
        die("the universe product count changed")
    #
    # ONE FIELD LEGITIMATELY CHANGES, and the guard says exactly which and how.
    # `qualification.reasons` carries homeowner-facing PROSE, one line of which
    # is "Supplier attribution is confirmed: Power Sheds." The rename must move
    # that sentence. Everything that DECIDES anything — status, confidenceTier,
    # priceEvidence, caveats, hardBlockers and the whole evidenceSignals block —
    # must be byte-identical. So `qualification` is compared sub-field by
    # sub-field, with `reasons` compared only after applying the rename, which
    # proves the ONLY difference in it is the supplier's name. This guard fired
    # on the first run and it was right: the naive whole-object compare could
    # not tell a decision change from a renamed sentence.
    DECISION_KEYS = ("status", "confidenceTier", "priceEvidence", "caveats",
                     "hardBlockers", "evidenceSignals")
    moved, prose = [], []
    for b, a in zip(before["products"], uni["products"]):
        if b.get("productId") != a.get("productId"):
            die("product order changed — ranking inputs are not comparable")
        for f in MATCH_FIELDS:
            if f == "qualification":
                qb, qa = b.get(f) or {}, a.get(f) or {}
                if sorted(qb) != sorted(qa):
                    die("qualification key set changed on %s" % a.get("productId"))
                for k in DECISION_KEYS:
                    if json.dumps(qb.get(k), sort_keys=True) != \
                       json.dumps(qa.get(k), sort_keys=True):
                        moved.append((a.get("productId"), "qualification." + k))
                rb = [rename(x) for x in (qb.get("reasons") or [])]
                ra = list(qa.get("reasons") or [])
                if rb != ra:
                    moved.append((a.get("productId"), "qualification.reasons"))
                elif (qb.get("reasons") or []) != ra:
                    prose.append(a.get("productId"))
                continue
            if json.dumps(b.get(f), sort_keys=True) != json.dumps(a.get(f), sort_keys=True):
                moved.append((a.get("productId"), f))
    if moved:
        die("MATCHING SURFACE MOVED — %d field(s), e.g. %s" % (len(moved), moved[:4]))
    if len(prose) != 3:
        die("expected the attribution sentence to be renamed on exactly 3 "
            "products, got %d: %s" % (len(prose), prose))
    for k in ("eligibleCount", "highConfidenceCount", "withCaveatCount",
              "limitedEvidenceCount", "excludedCount", "organisationCount",
              "governedDigest", "governedPriceContractVersion",
              "qualificationRuleVersion"):
        if before.get(k) != uni.get(k):
            die("universe header field %r changed: %r -> %r"
                % (k, before.get(k), uni.get(k)))
    print("  G8  matching surface byte-identical across all 573        OK")
    print("      price, tier, qualification DECISION, evidenceSignals, VAT,")
    print("      features, counts, governedDigest, rule version — none moved.")
    print("      The only change: the attribution SENTENCE on %d products,"
          % len(prose))
    print("      renamed and nothing else. Verified by rename-normalised compare.")

    # ---- guard 9 · NO OTHER SUPPLIER TOUCHED
    def orgs(d):
        return sorted({p.get("organisation") for p in d["products"]} - {None})
    ob, oa = set(orgs(before)), set(orgs(uni))
    if ob - {OLD} != oa - {NEW}:
        die("the set of organisations changed beyond the rename: %s / %s"
            % (sorted(ob - {OLD} - (oa - {NEW})), sorted(oa - {NEW} - (ob - {OLD}))))
    before_rights = json.loads((ROOT / "image-rights-manifest.json")
                               .read_text(encoding="utf-8"))
    after_rights = json.loads(out["image-rights-manifest.json"])
    bo = [r.get("organisation_name") for r in before_rights["rows"]]
    ao = [r.get("organisation_name") for r in after_rights["rows"]]
    if [x for x in bo if x != OLD] != [x for x in ao if x != NEW]:
        die("another supplier's rights row changed")
    if len(bo) != len(ao):
        die("the rights manifest row count changed")
    print("  G9  no other supplier changed: %d orgs, %d rights rows     OK"
          % (len(oa), len(ao)))

    # ---- guard 10 · the historical phase artefacts are not touched at all
    for d in MUST_NOT_CHANGE:
        if not d.exists():
            continue
        for rel in out:
            try:
                if pathlib.Path(rel).resolve().is_relative_to(d.resolve()):
                    die("this builder would write inside %s, which is "
                        "historical and must not change" % d.name)
            except (ValueError, OSError):
                pass
    print("  G10 writes nothing inside shadow-budget-v2 or 09 Commercial OK")

    if check:
        print("\n  --check: every guard passed. Nothing written.")
        return

    for rel in ROOT_JSON + [PAGE, IMAGERY]:
        (ROOT / rel).write_text(out[rel], encoding="utf-8")
    for p in (MODULE, GO_MANIFEST, GO_MODULE, GO_GUARD):
        p.write_text(out[str(p)], encoding="utf-8")

    print("\n  WRITTEN")
    for rel in ROOT_JSON + [PAGE, IMAGERY]:
        print("    %-46s %s" % (rel, sha16(ROOT / rel)))
    for p in (MODULE, GO_MANIFEST, GO_MODULE, GO_GUARD):
        print("    %-46s %s" % (p.name, sha16(p)))
    print("\n  Credit is now %r on every coupled surface." % NEW_CREDIT)
    print("  RE-RUN THE GATE: node atlas-tools/validate-image-rights.js "
          "--scan-html . --permissions image-rights-manifest.json")


if __name__ == "__main__":
    main()
