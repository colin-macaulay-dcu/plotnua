#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CAPABILITY PROOF — atlas-tools/prove-preview-only-containment.mjs.

The containment proof gained a second imagery mode on 2 October 2026, for
OGNYX, who invited imagery for their preview while withholding publication.

RE-AIMED 14 OCTOBER 2026. OGNYX graduated to a publication grant and left the
register, so no real supplier uses the preview-only mode today. The branch is
still live code, so it is still proved -- against a SYNTHETIC FIXTURE that is
installed before every case and removed after it: one register row, one rights
row and one decoy preview page, all named "ZZ Capability Fixture" on the
reserved .invalid domain. Nothing about the fixture survives the run, and the
hash line proves it.
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
PREVIEW = ROOT / "zz-capability-fixture-preview.html"
FIX_NAME = "ZZ Capability Fixture"
FIX_HOST = "capability-fixture.invalid"
FIX_IMG = "https://" + FIX_HOST + "/cdn/files/"
FIX_ROW = {
    "name": FIX_NAME, "imagery_mode": "preview-only", "page": PREVIEW.name,
    "site_host": FIX_HOST, "credit": "\u00a9 " + FIX_NAME,
    "image_hosts": [{"host": FIX_HOST, "path_prefix": "/cdn/", "why": "synthetic fixture"}],
    "imagery_evidence": "Synthetic capability fixture; never a real supplier.",
    "forbidden_claims": ["guaranteed"],
}
FIX_RECORD = {
    "organisation_name": FIX_NAME,
    "permission_outcome": "Granted with Conditions \u2014 Founder Confirmed",
    "permitted_domain": FIX_HOST, "required_credit": "\u00a9 " + FIX_NAME,
    "conditions": ["PREVIEW ONLY: imagery on " + PREVIEW.name + " and nowhere else."],
}
FIX_PAGE = ('<!doctype html><html><head><meta name="robots" content="noindex, '
            'nofollow, noarchive, nosnippet, noimageindex"></head><body>'
            '<p>\u00a9 ' + FIX_NAME + '</p><a href="https://' + FIX_HOST + '/">site</a>'
            '<img src="' + FIX_IMG + 'a.png" alt=""><img src="' + FIX_IMG + 'b.png" alt="">'
            '</body></html>')
PROOF = HERE / "prove-preview-only-containment.mjs"
DECOY = ROOT / "zz-capability-decoy.html"

TOUCHED = [REGISTER, RECORDS]
if PREVIEW.exists():
    print("refusing: a fixture page is already on disk: " + PREVIEW.name)
    sys.exit(2)
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


def install_fixture():
    edit_register(lambda d: d["suppliers"].append(dict(FIX_ROW)))
    d = json.loads(RECORDS.read_text(encoding="utf-8"))
    d["records"].append(dict(FIX_RECORD))
    RECORDS.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n",
                       encoding="utf-8")
    PREVIEW.write_text(FIX_PAGE, encoding="utf-8")


def case(label, mutate, expect):
    """mutate() changes the tree; everything is restored afterwards."""
    saved = {f: f.read_bytes() for f in TOUCHED}
    try:
        install_fixture()
        mutate()
        got, detail = containment()
    finally:
        for f, b in saved.items():
            f.write_bytes(b)
        for extra in (DECOY, PREVIEW):
            if extra.exists():
                extra.unlink()
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
    """The preview-only row under test: the synthetic fixture (see header)."""
    return [s for s in d["suppliers"] if s["name"] == FIX_NAME][0]


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
r(case("a preview-only image appears on a second page",
       lambda: DECOY.write_text(
           '<!doctype html><html><body><img src="'
           + FIX_IMG + 'x.png" alt=""></body></html>',
           encoding="utf-8"),
       "BREACHED"))

# ---- the stale row --------------------------------------------------------
# Without this the register could describe imagery that is no longer there,
# and "confined" would be true the way an empty room is tidy.
r(case("the preview loses the imagery the row permits",
       lambda: PREVIEW.write_text(
           PREVIEW.read_text(encoding="utf-8")
           .replace(FIX_IMG, "about:blank#"),
           encoding="utf-8"),
       "BREACHED"))

# ---- the rights record the mode depends on -------------------------------
def drop_condition(needle):
    def go():
        d = json.loads(RECORDS.read_text(encoding="utf-8"))
        for rec in d["records"]:
            if rec.get("organisation_name") == FIX_NAME:
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
                    if x.get("organisation_name") != FIX_NAME]
    RECORDS.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n",
                       encoding="utf-8")


r(case("the rights record disappears entirely",
       remove_record, "BREACHED"))

# ---- the fixture alone is contained, and so is the untouched tree --------
print("-" * 78)
r(case("CONTROL the installed fixture is contained", lambda: None, "CONTAINED"))
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
