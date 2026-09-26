#!/usr/bin/env python3
"""Proves the fixture exclusion actually bites, and that it bites NOTHING else.

A count filter is dangerous in both directions: too loose and a fixture inflates
a published figure, too tight and it silently deletes a real supplier. Both are
tested.
"""
import sys
from atlas_exclusions import EXCLUDED_RECORD_IDS, drop_excluded, is_excluded

FIXTURE = "recFiK85wMsREJ3AY"          # ORG-TEST-001
REAL = [
    ("recztK0C8LeTavhVJ", "TRIQBRIQ AG"),
    ("recuvqPv7XW0b0PFJ", "Nua Modular"),
    ("recyfWvDVODL06P8l", "Yardbox"),
    ("recQECqmQ2wTgWRNU", "Luka Nest"),
    ("recFjDMndB3sXWvIg", "INTUMODULAR"),
    ("recyvk5qXIB0aIzYR", "TeachNua Modular Living"),
]

fails = []

# 1 · the fixture is excluded
if not is_excluded(FIXTURE):
    fails.append("the test fixture is NOT excluded")

# 2 · every real organisation survives
for rid, name in REAL:
    if is_excluded(rid):
        fails.append(f"a REAL organisation is being excluded: {name} ({rid})")

# 3 · the filter removes exactly one record from a mixed batch
batch = [{"id": FIXTURE}] + [{"id": r} for r, _ in REAL]
kept, dropped = drop_excluded(batch)
if len(dropped) != 1 or dropped[0]["id"] != FIXTURE:
    fails.append(f"expected exactly the fixture dropped, got {[d['id'] for d in dropped]}")
if len(kept) != len(REAL):
    fails.append(f"expected {len(REAL)} kept, got {len(kept)}")

# 4 · the input is not mutated
if len(batch) != len(REAL) + 1:
    fails.append("drop_excluded mutated its input")

# 5 · nothing is excluded by NAME. A supplier called "Test Buildings Ltd" must
#     survive, which is exactly what a pattern-matching filter would break.
kept2, dropped2 = drop_excluded([{"id": "recREALTESTNAME01",
                                  "fields": {"Organisation Name": "Test Buildings Ltd"}}])
if dropped2:
    fails.append("a real organisation was excluded on its NAME, not its id")

# 6 · every reason is substantive, so a future reader can judge the exclusion
for rid, reason in EXCLUDED_RECORD_IDS.items():
    if len(reason) < 80:
        fails.append(f"{rid}: the exclusion reason is too thin to audit")

print("ATLAS EXCLUSION TEST")
print("=" * 66)
print(f"  excluded ids       : {len(EXCLUDED_RECORD_IDS)}")
print(f"  real orgs checked  : {len(REAL)}, all survive")
for f in fails:
    print(f"  FAIL  {f}")
print("=" * 66)
print("PASS" if not fails else f"{len(fails)} FAILURE(S)")
sys.exit(1 if fails else 0)
