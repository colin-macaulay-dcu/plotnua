#!/usr/bin/env python3
"""Apply the founder-approved DISC-032 provenance declaration to image-provenance-records.json.

    python3 atlas-tools/declare-disc032-provenance.py                 # dry run (records)
    python3 atlas-tools/declare-disc032-provenance.py --write         # writes the register

Reads governance/DISC-032-PROVENANCE-DECLARATION-2026-10-27.json. The founder approved the image
pair, the provenance chain, the tolerance exception and the corrected record on 27 Oct 2026, and
instructed (Phase 2, item 6) that the declaration be applied only after its contents are validated.
This script is that validation; it never writes a classification of its own:

  * the declaration names its approvals, signer and date, and states no prompt (prompts were not
    supplied: prompt_status UNAVAILABLE, never reconstructed) and no reference_inputs (UNCERTAIN);
  * every record is AI_ILLUSTRATION, founder-attested form, decision PN-FDR-2026-10-27-DISC032,
    surfaces exactly discovery + library-card, a named human review, and a resemblance review;
  * every file is re-hashed from disk and must equal the declared sha256 and byte size, and every
    declared master hash must equal the masters of record;
  * the v3 records must say v3 carries no OpenAI credentials; no record may claim it does;
  * a record already in the register is refused.

validate-image-provenance.js then decides whether the result publishes (P1-P14), with the
nine encodings pinned by SHA-256 in FOUNDER_ATTESTED_DISC032.
"""
import hashlib, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REG = os.path.join(ROOT, "image-provenance-records.json")
DEC = os.path.join(ROOT, "governance", "DISC-032-PROVENANCE-DECLARATION-2026-10-27.json")
DECISION = "PN-FDR-2026-10-27-DISC032"
MASTERS = {"5b480b06cb181c7b06ea4f36fbd2a73d84207dba3aa8727cc87067090c746d7f": 2255134,   # C1 v3, BEFORE
           "c1ec36632d451536aaf41c001f09301914b05898767bbcff13784f3d71f8ab78": 2241019}   # C2, POSSIBLE
V2 = "993a7393d62bea36b34ded358688d768c939d0c5024d198e7f34e76aabdbbed3"


def die(msg):
    sys.exit("REFUSED: " + msg)


def main():
    write, launch = "--write" in sys.argv, "--launch" in sys.argv
    dec = json.load(open(DEC, encoding="utf-8"))
    if dec.get("decision") != DECISION:
        die("the declaration is not %s" % DECISION)
    ans = dec.get("answers") or {}
    for k in ("signed_by", "date", "tool"):
        if not str(ans.get(k) or "").strip():
            die("answers.%s is empty" % k)
    if len(dec.get("founder_approvals") or []) < 3:
        die("the three founder approvals of 27 Oct 2026 are not all recorded")
    rows = dec.get("launch_records", []) if launch else dec["records"]
    reg = json.load(open(REG, encoding="utf-8"))
    have = {r["asset"] for r in reg["records"]}
    new = []
    for r in rows:
        a = r["asset"]
        if r.get("class") != "AI_ILLUSTRATION":
            die("%s: not AI_ILLUSTRATION" % a)
        if "prompt" in r or "reference_inputs" in r:
            die("%s: a prompt or reference_inputs is stated; none was supplied" % a)
        if r.get("prompt_status") != "UNAVAILABLE":
            die("%s: prompt_status is not UNAVAILABLE" % a)
        rd, rv, hr = r.get("reference_disclosure") or {}, r.get("resemblance_review") or {}, r.get("human_review") or {}
        if rd.get("status") != "UNCERTAIN" or not rd.get("statement") or not rd.get("evidence"):
            die("%s: the reference uncertainty is not disclosed" % a)
        if not (rv.get("date") and rv.get("compared_against") and rv.get("verdict") and rv.get("findings")):
            die("%s: no resemblance review" % a)
        if not (hr.get("reviewer") and hr.get("date") and hr.get("attests")):
            die("%s: no named human review" % a)
        if DECISION not in str(r.get("decision_ref", "")):
            die("%s: no %s" % (a, DECISION))
        if r.get("permitted_surfaces") != ["discovery", "library-card"]:
            die("%s: surfaces are not exactly discovery + library-card" % a)
        if r.get("depicts_named_product") is not False or r.get("depicts_named_organisation") is not False:
            die("%s: depicts a named product or organisation" % a)
        m = r["generated"]["source_master"]
        if MASTERS.get(m["sha256"]) != m["bytes"]:
            die("%s: the source master is not a master of record" % a)
        blob = json.dumps(r)
        if m["sha256"].startswith("5b480b06"):
            if V2 not in blob or "NONE" not in json.dumps(r["generated"]["c2pa_evidence"]["v3_master"]["openai_c2pa"]):
                die("%s: the v3 chain to v2, or v3's absence of OpenAI credentials, is not stated" % a)
        if "DRAFT" in blob or "FOUNDER TO CONFIRM" in blob or "PENDING" in blob:
            die("%s: carries draft wording" % a)
        p = os.path.join(ROOT, a)
        if not os.path.exists(p):
            die("%s: not on disk" % a)
        d = open(p, "rb").read()
        if hashlib.sha256(d).hexdigest() != r["sha256"] or len(d) != r["bytes"]:
            die("%s: the file on disk is not the file that was declared" % a)
        if a in have:
            die("%s: already declared" % a)
        new.append(r)
    print("DISC-032 provenance: %d record(s) validated%s" % (len(new), " (launch: Library card)" if launch else ""))
    for r in new:
        print("  + %s  %s" % (r["asset"], r["sha256"][:12]))
    if not write:
        print("dry run: nothing written (add --write)")
        return
    reg["records"].extend(new)
    open(REG, "w").write(json.dumps(reg, indent=2) + "\n")   # the register's own format
    print("written: image-provenance-records.json. Now run: node atlas-tools/validate-image-provenance.js")


if __name__ == "__main__":
    main()
