#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUARD-CAPABILITY PROOF for generate_image_rights_manifest.py --check.

--check was changed to exempt the manifest's 'generated' date from the drift
comparison, because including today's date made the check fail every day but
one. An exemption is exactly the kind of change that can quietly widen into
"ignores everything". A relaxed check that has never been seen to refuse is a
comment, not a gate.

So this breaks it once per claim and requires every break to be caught.

    1  a permission outcome downgraded in the records     must refuse
    2  a permitted_domain widened in the records          must refuse
    3  a row hand-edited in the manifest                  must refuse
    4  the manifest's reality_note hand-softened          must refuse
    5  manifest reformatted (indent changed)              must refuse
    6  ONLY the date differs                              must PASS
    7  the stamp dated in the future                      must refuse
    8  the stamp missing                                  must refuse
    9  the stamp not an ISO date                          must refuse
   10  the manifest not valid JSON                        must refuse
   11  no manifest at all                                 must refuse

Case 6 is the point of the exemption and the only one that must pass. The other
ten are what stops the exemption from having eaten the gate.

Every case runs in its own temporary tree. The repository's own records,
manifest and generator are hashed before and after and must be unchanged: a
proof that edits the thing it is proving has proved nothing.
"""

import datetime
import hashlib
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
REPO = HERE.parent.parent
GEN = HERE / "generate_image_rights_manifest.py"
RECORDS = REPO / "image-rights-records.json"
MANIFEST = REPO / "image-rights-manifest.json"

WATCHED = [GEN, RECORDS, MANIFEST]


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def tree():
    """A throwaway copy of just the three files --check touches."""
    d = pathlib.Path(tempfile.mkdtemp(prefix="manifest-check-proof-"))
    (d / ".github" / "scripts").mkdir(parents=True)
    shutil.copy2(GEN, d / ".github" / "scripts" / GEN.name)
    shutil.copy2(RECORDS, d / RECORDS.name)
    shutil.copy2(MANIFEST, d / MANIFEST.name)
    return d


def run_check(d):
    r = subprocess.run(
        [sys.executable, str(d / ".github" / "scripts" / GEN.name), "--check"],
        capture_output=True, text=True, cwd=str(d))
    return r.returncode, (r.stdout + r.stderr)


def load(p):
    return json.loads(p.read_text(encoding="utf-8"))


def dump(p, obj):
    p.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n",
                 encoding="utf-8")


# --------------------------------------------------------------- the sabotages

def s01_downgrade_outcome(d):
    """A live grant turned into a non-grant. The gate's whole purpose."""
    obj = load(d / RECORDS.name)
    for r in obj["records"]:
        if r["permission_outcome"] == "Granted — Founder Confirmed":
            r["permission_outcome"] = "Withdrawn / Superseded"
            break
    else:
        raise AssertionError("no founder-confirmed grant to downgrade")
    dump(d / RECORDS.name, obj)


def s02_widen_domain(d):
    obj = load(d / RECORDS.name)
    for r in obj["records"]:
        if r.get("permitted_domain"):
            r["permitted_domain"] = "example.com"
            break
    else:
        raise AssertionError("no permitted_domain to widen")
    dump(d / RECORDS.name, obj)


def s03_handedit_manifest_row(d):
    obj = load(d / MANIFEST.name)
    obj["rows"][0]["permitted_domain"] = "attacker.example"
    dump(d / MANIFEST.name, obj)


def s04_soften_reality_note(d):
    obj = load(d / MANIFEST.name)
    obj["reality_note"] = "All supplier imagery is fine to publish."
    dump(d / MANIFEST.name, obj)


def s05_reformat(d):
    obj = load(d / MANIFEST.name)
    (d / MANIFEST.name).write_text(
        json.dumps(obj, indent=4, ensure_ascii=False) + "\n", encoding="utf-8")


def s06_date_only(d):
    """The ONE case that must pass. Nothing but the stamp differs."""
    obj = load(d / MANIFEST.name)
    obj["generated"] = "2020-01-01"
    dump(d / MANIFEST.name, obj)


def s07_future_stamp(d):
    obj = load(d / MANIFEST.name)
    ahead = datetime.date.today() + datetime.timedelta(days=365)
    obj["generated"] = ahead.isoformat()
    dump(d / MANIFEST.name, obj)


def s08_stamp_missing(d):
    obj = load(d / MANIFEST.name)
    del obj["generated"]
    dump(d / MANIFEST.name, obj)


def s09_stamp_not_iso(d):
    obj = load(d / MANIFEST.name)
    obj["generated"] = "last Tuesday"
    dump(d / MANIFEST.name, obj)


def s10_not_json(d):
    (d / MANIFEST.name).write_text("{ this is not json", encoding="utf-8")


def s11_no_manifest(d):
    (d / MANIFEST.name).unlink()


CASES = [
    ("01 a live grant downgraded in the records", s01_downgrade_outcome, "refuse"),
    ("02 a permitted_domain widened in the records", s02_widen_domain, "refuse"),
    ("03 a manifest row hand-edited", s03_handedit_manifest_row, "refuse"),
    ("04 the reality_note hand-softened", s04_soften_reality_note, "refuse"),
    ("05 the manifest reformatted", s05_reformat, "refuse"),
    ("06 ONLY the generated date differs", s06_date_only, "pass"),
    ("07 the stamp dated in the future", s07_future_stamp, "refuse"),
    ("08 the stamp missing", s08_stamp_missing, "refuse"),
    ("09 the stamp not an ISO date", s09_stamp_not_iso, "refuse"),
    ("10 the manifest not valid JSON", s10_not_json, "refuse"),
    ("11 no manifest at all", s11_no_manifest, "refuse"),
]


def main():
    before = {p: sha(p) for p in WATCHED}

    print("=" * 78)
    print("GUARD-CAPABILITY PROOF — generate_image_rights_manifest.py --check")
    print("=" * 78)

    # Baseline: unsabotaged, the check must pass. Without this, every "refuse"
    # below could be the check refusing for some unrelated reason.
    d = tree()
    try:
        code, out = run_check(d)
        if code != 0:
            print("\nFAIL baseline: --check refuses an untouched tree")
            print(out)
            return 1
        print("\n  PASS   baseline — untouched tree, --check exits 0")
    finally:
        shutil.rmtree(d, ignore_errors=True)

    failures = []
    for label, sabotage, expect in CASES:
        d = tree()
        try:
            sabotage(d)
            code, out = run_check(d)
            ok = (code == 0) if expect == "pass" else (code != 0)
            verdict = "PASS  " if ok else "FAIL  "
            print("  %s %s  [expected %s, exit %d]"
                  % (verdict, label, expect, code))
            if not ok:
                failures.append((label, expect, code, out.strip()))
        finally:
            shutil.rmtree(d, ignore_errors=True)

    after = {p: sha(p) for p in WATCHED}
    print()
    for p in WATCHED:
        same = before[p] == after[p]
        print("  %s %s" % ("PASS  " if same else "FAIL  ",
                           "unchanged by this proof: " + p.name))
        if not same:
            failures.append((p.name + " was modified", "unchanged", -1, ""))

    print()
    if failures:
        print("=" * 78)
        print("CAPABILITY NOT PROVED — %d case(s) behaved wrongly" % len(failures))
        for label, expect, code, out in failures:
            print("\n--- %s (expected %s, exit %s)" % (label, expect, code))
            print(out)
        return 1

    print("=" * 78)
    print("CAPABILITY PROVED — the date stamp is exempt and NOTHING ELSE is.")
    print("Ten ways of changing the rights, the rows, the wording, the")
    print("formatting or the stamp's own honesty are each refused; only a")
    print("difference of date alone passes.")
    print("=" * 78)
    return 0


if __name__ == "__main__":
    sys.exit(main())
