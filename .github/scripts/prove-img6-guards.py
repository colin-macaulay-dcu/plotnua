#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GUARD-CAPABILITY PROOF — build-img6-three-supplier-grants.py.

A guard that has never refused anything is a comment. This breaks the builder
once per guard and every break must be caught.

The builder runs in --check mode throughout, so image-rights-records.json is
never written by this proof. It is hashed before and after and the hash is
printed: a proof that damages what it proves is worse than no proof.

ONE SABOTAGE CHANNEL is enough here, unlike the Results proofs: every guard in
this builder reads the NEW list, which the builder itself holds, so patching
the builder's own source reaches all of them. The records file is read only to
count what is already there, and R01 is broken through the builder's own
expected count rather than by touching the real file.

Run: python3 .github/scripts/prove-img6-guards.py
"""

import contextlib
import hashlib
import io
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
BUILDER = HERE / "build-img6-three-supplier-grants.py"
RECORDS = HERE.parent.parent / "image-rights-records.json"

before = hashlib.sha256(RECORDS.read_bytes()).hexdigest()
_n = [0]


def run(label, subs=(), expect="REFUSED"):
    code = BUILDER.read_text(encoding="utf-8")
    for old, new in subs:
        if old not in code:
            raise AssertionError("builder anchor absent: %r" % old[:70])
        code = code.replace(old, new, 1)
    argv, buf, rc = sys.argv, io.StringIO(), 0
    sys.argv = [str(BUILDER), "--check"]
    _n[0] += 1
    try:
        with contextlib.redirect_stdout(buf):
            g = {"__name__": "__main__", "__file__": str(BUILDER)}
            exec(compile(code, str(BUILDER), "exec"), g)
    except SystemExit as e:
        rc = e.code or 0
    finally:
        sys.argv = argv
    out = [l for l in buf.getvalue().strip().splitlines() if l.startswith("REFUSED")]
    got = "REFUSED" if rc else "BUILT"
    hit = got == expect
    print("  %s %-7s %s" % ("CAUGHT " if hit else "MISSED ", got, label))
    print("           -> %s" % (out[0][:112] if out else "(no refusal printed)"))
    return hit


print("GUARD-CAPABILITY PROOF — IMG-6 THREE SUPPLIER GRANTS")
print("=" * 78)
r = []

# ---- R00 . idempotence ------------------------------------------------------
r.append(run("R00 . an organisation already in the file is offered again",
             [('"organisation_record": "recUrpkOqKbynjQP0"',
               '"organisation_record": "recTq78jSQNOluU8c"')]))

# ---- R01 . the file is the one the builder was anchored against -------------
r.append(run("R01 . the prior record count has moved",
             [("len(records) == 6", "len(records) == 5")]))

# ---- R02 . vocabulary -------------------------------------------------------
r.append(run("R02 . an outcome is spelled loosely rather than exactly",
             [('"permission_outcome": "Granted with Conditions — Founder Confirmed",\n'
               '        "permitted_domain": "gardenroomireland.ie"',
               '"permission_outcome": "Granted, probably",\n'
               '        "permitted_domain": "gardenroomireland.ie"')]))

# ---- R03a . a foreign Wix account is granted -------------------------------
r.append(run("R03a . a foreign Wix account prefix is granted outright",
             [('"path_prefix": "/media/fef4b6_",',
               '"path_prefix": "/media/11062b_",')]))

# ---- R03b . the bare shared CDN --------------------------------------------
r.append(run("R03b . the Wix scope is widened to the bare /media/ path",
             [('"path_prefix": "/media/fef4b6_",', '"path_prefix": "/media/",')]))

# ---- R04 . the shape of Garden Room Ireland's scope -------------------------
# Broken with a THIRD entry whose prefix is itself legitimate, so neither R03a
# nor R03b can catch it first and R04 has to refuse on its own. This is the
# case that matters: a scope quietly growing an extra arm nobody granted.
r.append(run("R04 . a third, individually-legitimate prefix is added to GRI",
             [('        ],\n        "required_credit": "© Garden Room Ireland",',
               '            ,{\n'
               '                "host": "static.wixstatic.com",\n'
               '                "path_prefix": "/media/fef4b6_extra",\n'
               '                "why": "not granted by anybody"\n'
               '            }\n'
               '        ],\n        "required_credit": "© Garden Room Ireland",')]))

# ---- R05a . Elm or Don quietly gains a delivery host ------------------------
r.append(run("R05a . Elm is given a delivery host it does not need",
             [('"permitted_domain": "elmlandscaping.ie",',
               '"permitted_domain": "elmlandscaping.ie",\n'
               '        "permitted_delivery_hosts": [{"host": "cdn.example.net",'
               ' "path_prefix": "/elm/", "why": "x"}],')]))

# ---- R05b . Instagram is admitted -------------------------------------------
r.append(run("R05b . the Instagram embed is admitted as a permitted domain",
             [('"permitted_domain": "elmlandscaping.ie",',
               '"permitted_domain": "scontent.cdninstagram.com",')]))

# ---- R06 . a live grant with no provenance ----------------------------------
r.append(run("R06 . Don's Atlas permission record is dropped",
             [('"atlas_permission_record": "recAFBJW5nwWv0Z20",', "")]))

r.append(run("R06 . Garden Room Ireland's required credit is dropped",
             [('"required_credit": "© Garden Room Ireland",', "")]))

# ---- R07 . the CGI fact is removed ------------------------------------------
r.append(run("R07 . the visualisation condition is removed from Don's record",
             [('"EVERY governed Don image is a computer-generated architectural '
               'visualisation, not a photograph of a completed build, and must '
               'never be presented as one."', '"Nothing in particular."')]))

# ---- the unmutated builder must still pass ----------------------------------
print("-" * 78)
r.append(run("the unmutated builder passes every guard", expect="BUILT"))

after = hashlib.sha256(RECORDS.read_bytes()).hexdigest()
print("=" * 78)
print("%d of %d checks passed" % (sum(1 for x in r if x), len(r)))
print("image-rights-records.json untouched by this proof: %s  (%s)"
      % ("YES" if before == after else "NO", after[:12]))
sys.exit(0 if all(r) and before == after else 1)
