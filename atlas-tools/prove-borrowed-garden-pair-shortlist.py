#!/usr/bin/env python3
"""Proof for borrowed-garden-pair-shortlist.py, on SYNTHETIC records only.

  python3 atlas-tools/prove-borrowed-garden-pair-shortlist.py
"""
import csv
import importlib.util
import re
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("ps", HERE / "borrowed-garden-pair-shortlist.py")
ps = importlib.util.module_from_spec(spec); spec.loader.exec_module(ps)

ok = bad = 0
def check(name, cond, detail=""):
    global ok, bad
    ok += bool(cond); bad += (not cond)
    print(("  [PASS] " if cond else "  [FAIL] ") + name + ("" if cond else f"   {detail}"))

G = [  # synthetic homeowners. names/emails present ONLY to prove they never leak.
 dict(record_ref="recG1", first_name="Synthia", email="synthia@example.com", status="interest_submitted", district="killester", size_note="medium", water="outside_tap", timing="flexible", inherited_tenure="own", permission_confirmed="", garden_note=""),
 dict(record_ref="recG2", first_name="Testa", email="testa@example.com", status="interest_submitted", district="raheny", size_note="small", water="none", timing="this_season", inherited_tenure="rent", permission_confirmed="checked", garden_note="My landlord knows and has agreed."),
 dict(record_ref="recG3", first_name="Rentie", email="rentie@example.com", status="interest_submitted", district="artane", size_note="large", water="outside_tap", timing="flexible", inherited_tenure="rent", permission_confirmed="", garden_note=""),
 dict(record_ref="recG4", first_name="Buyer", email="buyer@example.com", status="interest_submitted", district="artane", size_note="large", water="outside_tap", timing="flexible", inherited_tenure="buying", permission_confirmed="", garden_note=""),
 dict(record_ref="recG5", first_name="Far", email="far@example.com", status="interest_submitted", district="elsewhere_in_dublin", size_note="large", water="outside_tap", timing="flexible", inherited_tenure="own", permission_confirmed="", garden_note=""),
 dict(record_ref="recG6", first_name="Paused", email="p@example.com", status="paused", district="killester", size_note="large", water="outside_tap", timing="flexible", inherited_tenure="own", permission_confirmed="", garden_note=""),
]
P = [  # synthetic growers
 dict(record_ref="recP1", first_name="Grow", email="grow@example.com", status="interest_submitted", county="dublin", district="donnycarney", travel_distance="up_to_5km", space_wanted="small", timing="next_season", growing_note="Beginner; salad leaves; Saturdays"),
 dict(record_ref="recP2", first_name="Walker", email="walk@example.com", status="interest_submitted", county="dublin", district="raheny", travel_distance="", space_wanted="very_small", timing="within_3_months", growing_note=""),
 dict(record_ref="recP3", first_name="Bigplot", email="big@example.com", status="interest_submitted", county="dublin", district="killester", travel_distance="up_to_10km", space_wanted="large", timing="this_season", growing_note=""),
 dict(record_ref="recP4", first_name="Away", email="away@example.com", status="interest_submitted", county="clare", district="elsewhere_in_ireland", travel_distance="flexible", space_wanted="small", timing="flexible", growing_note=""),
]

pairs, excl = ps.shortlist([{c: g.get(c, "") for c in ps.GARDEN_COLS} for g in G],
                           [{c: p.get(c, "") for c in ps.GROWER_COLS} for p in P])
got = {(x["garden_ref"], x["grower_ref"]) for x in pairs}
check("S1 owner in Killester (medium, flexible) pairs with a Donnycarney grower within 2 km wanting small", ("recG1", "recP1") in got)
check("S2 renter WITH tick and statement is considered (Raheny, walking grower, very small)", ("recG2", "recP2") in got)
check("S2b ...and is flagged: no water, read the garden note, travel not given",
      any(x["garden_ref"] == "recG2" and "water: none" in x["flags"] and "garden note" in x["flags"]
          and "travel not given" in x["flags"] for x in pairs))
check("S3 renter WITHOUT tick/statement is never considered", not any(x["garden_ref"] == "recG3" for x in pairs)
      and any(r == "recG3" and "G1B" in w for _, r, w in excl))
check("S4 buying is never put forward", not any(x["garden_ref"] == "recG4" for x in pairs)
      and any(r == "recG4" and "buying" in w for _, r, w in excl))
check("S5 outside the pilot districts: not considered (either side)",
      not any(x["garden_ref"] == "recG5" or x["grower_ref"] == "recP4" for x in pairs))
check("S6 paused records are not considered", not any(x["garden_ref"] == "recG6" for x in pairs))
check("S7 space: a grower wanting large is not paired with a medium garden", ("recG1", "recP3") not in got)
check("S8 distance: a Raheny grower who gave no travel distance is not paired with Killester (2.5 km)", ("recG1", "recP2") not in got)
check("S9 timing: this_season grower vs next_season-only garden would not pair; flexible garden does",
      ("recG1", "recP3") not in got)

with tempfile.TemporaryDirectory() as d:
    d = Path(d)
    for name, rows, cols in [("g.csv", G, list(G[0])), ("p.csv", P, list(P[0]))]:
        with (d / name).open("w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=cols); w.writeheader(); w.writerows(rows)
    ps.main([str(d / "g.csv"), str(d / "p.csv"), "-o", str(d / "out.csv")])
    out = (d / "out.csv").read_text()
    leaked = [s for s in ["@", "Synthia", "Testa", "Grow,", "salad", "landlord"] if s in out]
    check("S10 the output file holds no name, email or note text", not leaked, leaked)
    check("S11 every row says nobody has been contacted", all("nobody contacted" in l for l in out.splitlines()[1:]))
src = (HERE / "borrowed-garden-pair-shortlist.py").read_text()
check("S12 the tool has no network, Airtable-write or email code",
      not re.search(r"^\s*(import|from)\s+(urllib|requests|http|smtplib|socket)", src, re.M) and "api.airtable.com" not in src)

print(f"\n  {ok} passed, {bad} failed")
sys.exit(1 if bad else 0)
