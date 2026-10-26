#!/usr/bin/env python3
"""Apply the founder-signed DISC-031 provenance declaration to image-provenance-records.json.

    python3 atlas-tools/declare-disc031-provenance.py SIGNED.json            # dry run
    python3 atlas-tools/declare-disc031-provenance.py SIGNED.json --write    # writes the register

SIGNED.json is governance/DISC-031-PROVENANCE-DECLARATION-DRAFT-2026-10-26.json after the founder has:
  * filled answers.signed_by, answers.date and answers.tool (the generator that made the masters);
  * answered C1 ("no" or "not-recorded") and C2 ("accept");
  * filled every record's human_review.reviewer and human_review.date, and replaced every
    "FOUNDER TO CONFIRM" and every "DRAFT" with his own confirmed wording.

If the founder has the prompts, he pastes each one into its records as "prompt" and gives C1 "no"
with an explicit "reference_inputs": []; the script then removes the founder-attested fields
(prompt_status, reference_disclosure, resemblance_review, decision_ref) so the record takes the
normal form. Otherwise the founder-attested form is kept, and validate-image-provenance.js accepts
it only for these exact files (FOUNDER_ATTESTED_DISC031, pinned by SHA-256, discovery and
library-card surfaces only).

It never writes a classification on its own: every record comes from the signed declaration, the
files are re-hashed from disk, and the validator's own rules decide whether the result publishes.
"""
import hashlib, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REG = os.path.join(ROOT, "image-provenance-records.json")
ATTESTED = ("prompt_status", "reference_disclosure", "resemblance_review", "decision_ref")


def die(msg):
    sys.exit("REFUSED: " + msg)


def sha(p):
    return hashlib.sha256(open(os.path.join(ROOT, p), "rb").read()).hexdigest()


def main():
    if len(sys.argv) < 2:
        die("usage: declare-disc031-provenance.py SIGNED.json [--write]")
    write = "--write" in sys.argv[2:]
    dec = json.load(open(sys.argv[1]))
    ans = dec.get("answers") or {}
    for k in ("signed_by", "date", "tool"):
        if not str(ans.get(k, "")).strip():
            die("the declaration is not signed: answers.%s is empty" % k)
    c1 = str(ans.get("C1", "")).lower()
    if c1 not in ("no", "not-recorded"):
        die('C1 must be "no" or "not-recorded"')
    if str(ans.get("C2", "")).lower() != "accept":
        die('C2 is not "accept": the resemblance review has not been accepted')

    reg = json.load(open(REG))
    have = {r["asset"] for r in reg["records"]}
    new = []
    for r in dec["records"]:
        rec = json.loads(json.dumps(r))
        hr = rec.get("human_review") or {}
        if not hr.get("reviewer") or not hr.get("date"):
            die("%s: human_review is not signed" % rec["asset"])
        rec["generated"]["tool"] = rec["generated"]["tool"].replace(
            "FOUNDER TO CONFIRM: the generative image tool used to make the master (not recorded in the build instruction of 26 Oct 2026)",
            ans["tool"].strip())
        if "prompt" in rec:                      # the normal form: the founder supplied the prompt
            if c1 != "no" or rec.get("reference_inputs") != []:
                die("%s: a prompt was supplied, so C1 must be \"no\" and reference_inputs must be []" % rec["asset"])
            for k in ATTESTED:
                rec.pop(k, None)
        else:
            rd = rec.get("reference_disclosure") or {}
            if c1 == "not-recorded" and (rd.get("status") != "UNCERTAIN" or "reference_inputs" in rec):
                die("%s: C1 is not-recorded, so the record must disclose the uncertainty" % rec["asset"])
            if "PENDING" in rec.get("decision_ref", ""):
                rec["decision_ref"] = rec["decision_ref"].replace("PENDING founder signature: ", "")
        blob = json.dumps(rec)
        if "FOUNDER TO CONFIRM" in blob or "DRAFT" in blob:
            die("%s: still carries draft wording" % rec["asset"])
        if sha(rec["asset"]) != rec["sha256"]:
            die("%s: the file on disk is not the file the founder signed" % rec["asset"])
        if rec["asset"] in have:
            die("%s: already declared" % rec["asset"])
        new.append(rec)
    print("DISC-031 provenance: %d record(s) to add" % len(new))
    for r in new:
        print("  + %s  %s" % (r["asset"], "normal form" if "prompt" in r else "founder-attested form"))
    if not write:
        print("dry run: nothing written (add --write)")
        return
    reg["records"].extend(new)
    open(REG, "w").write(json.dumps(reg, indent=2) + "\n")   # the register's own format
    print("written: image-provenance-records.json. Now run: node atlas-tools/validate-image-provenance.js")


if __name__ == "__main__":
    main()
