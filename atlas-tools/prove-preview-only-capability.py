#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CAPABILITY PROOF — atlas-tools/prove-preview-only-containment.mjs.

The containment proof gained a second imagery mode on 2 October 2026, for
OGNYX, who invited imagery for their preview while withholding publication.
That branch is new code, and a guard that has never refused anything is a
comment. This breaks the containment proof once per check and every break
must be caught.

HOW. The register, the rights records and the pages are real files, so each
sabotage is applied IN PLACE, the containment proof is run as a subprocess,
and the file is restored from an in-memory copy in a finally block. Every
touched file is hashed before the first sabotage and after the last, and the
hashes are printed: a proof that damages what it proves is worse than no
proof. If this script is killed mid-run, `git status` will show exactly what
to revert, and the hash line will not print.

WHAT IS BEING PROVED. Not that containment holds -- the containment proof
itself says that. This proves that the containment proof would NOTICE if it
stopped holding, which is a different claim and the one that matters.

Run: python3 atlas-tools/prove-preview-only-capability.py
"""

import hashlib
import json
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
REGISTER = HERE / "preview-only-suppliers.json"
RECORDS = ROOT / "image-rights-records.json"
PREVIEW = ROOT / "ognyx-preview.html"
PROOF = HERE / "prove-preview-only-containment.mjs"
DECOY = ROOT / "zz-capability-decoy.html"

TOUCHED = [REGISTER, RECORDS, PREVIEW]
for f in TOUCHED + [PROOF]:
    if not f.exists():
        print("missing: " + str(f))
        sys.exit(2)

before = {f: hashlib.sha256(f.read_bytes()).hexdigest() for f in TOUCHED}
results = []


def containment():
    """Returns ('CONTAINED' | 'BREACHED' | 'NOT ESTABLISHED', first line)."""
    p = subprocess.run(["node", str(PROOF)], capture_output=True, text=True,
                       cwd=str(ROOT))
    verdict = {0: "CONTAINED", 1: "BREACHED"}.get(p.returncode,
                                                  "NOT ESTABLISHED")
    detail = ""
    for line in p.stdout.splitlines():
        t = line.strip()
        if t.startswith("FAIL") or t.startswith("ERROR"):
            detail = t
            break
    return verdict, detail


def case(label, mutate, expect):
    """mutate() changes the tree; everything is restored afterwards."""
    saved = {f: f.read_bytes() for f in TOUCHED}
    try:
        mutate()
        got, detail = containment()
    finally:
        for f, b in saved.items():
            f.write_bytes(b)
        if DECOY.exists():
            DECOY.unlink()
    hit = got == expect
    print("  %s %-16s %s" % ("CAUGHT " if hit else "MISSED ", got, label))
    print("          -> %s" % (detail[:104] if detail else "(nothing reported)"))
    return hit


def edit_register(fn):
    d = json.loads(REGISTER.read_text(encoding="utf-8"))
    fn(d)
    REGISTER.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8")


def ognyx(d):
    return [s for s in d["suppliers"] if s["name"] == "OGNYX"][0]


print("CAPABILITY PROOF — PREVIEW-ONLY CONTAINMENT")
print("=" * 78)
r = results.append

# ---- the mode itself ------------------------------------------------------
# THE PERMISSIVE READING OF A TYPO IS THE DANGEROUS ONE. A row whose mode is
# missing or misspelt must not fall through to either branch.
r(case("imagery_mode is removed from the OGNYX row",
       lambda: edit_register(lambda d: ognyx(d).pop("imagery_mode", None)),
       "NOT ESTABLISHED"))

r(case("imagery_mode is misspelt 'preview_only'",
       lambda: edit_register(
           lambda d: ognyx(d).__setitem__("imagery_mode", "preview_only")),
       "NOT ESTABLISHED"))

# ---- the branch boundary --------------------------------------------------
# A supplier who granted nothing must not be able to carry imagery by being
# in the register at all. Flipping OGNYX to "none" while the page still shows
# their images is that mistake made deliberately.
r(case("a page carries imagery while the mode says none was granted",
       lambda: edit_register(
           lambda d: ognyx(d).__setitem__("imagery_mode", "none")),
       "BREACHED"))

# ---- confinement ----------------------------------------------------------
# The whole point of the mode: their imagery on their page and nowhere else.
r(case("an OGNYX image appears on a second page",
       lambda: DECOY.write_text(
           '<!doctype html><html><body><img src="'
           'https://www.ognyx.com/cdn/shop/files/x.png" alt=""></body></html>',
           encoding="utf-8"),
       "BREACHED"))

# ---- the stale row --------------------------------------------------------
# Without this the register could describe imagery that is no longer there,
# and "confined" would be true the way an empty room is tidy.
r(case("the preview loses the imagery the row permits",
       lambda: PREVIEW.write_text(
           PREVIEW.read_text(encoding="utf-8")
           .replace("https://www.ognyx.com/cdn/shop/files/", "about:blank#"),
           encoding="utf-8"),
       "BREACHED"))

# ---- the rights record the mode depends on -------------------------------
def drop_condition(needle):
    def go():
        d = json.loads(RECORDS.read_text(encoding="utf-8"))
        for rec in d["records"]:
            if rec.get("organisation_name") == "OGNYX":
                rec["conditions"] = [c for c in rec["conditions"]
                                     if needle not in c.lower()]
        RECORDS.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n",
                           encoding="utf-8")
    return go


r(case("the PREVIEW ONLY condition is dropped from the rights record",
       drop_condition("preview only"), "BREACHED"))


def remove_record():
    d = json.loads(RECORDS.read_text(encoding="utf-8"))
    d["records"] = [x for x in d["records"]
                    if x.get("organisation_name") != "OGNYX"]
    RECORDS.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n",
                       encoding="utf-8")


r(case("the rights record disappears entirely",
       remove_record, "BREACHED"))

# ---- and the untouched tree must still be contained ----------------------
print("-" * 78)
got, _ = containment()
hit = got == "CONTAINED"
r(hit)
print("  %s %-16s the untouched tree is contained" %
      ("CAUGHT " if hit else "MISSED ", got))

after = {f: hashlib.sha256(f.read_bytes()).hexdigest() for f in TOUCHED}
intact = all(before[f] == after[f] for f in TOUCHED)
print("=" * 78)
print("%d of %d checks passed" % (sum(1 for x in results if x), len(results)))
print("every touched file is byte-identical after the proof: %s"
      % ("YES" if intact else "NO"))
for f in TOUCHED:
    print("  %-34s %s" % (f.name, after[f][:12]))
sys.exit(0 if all(results) and intact else 1)
