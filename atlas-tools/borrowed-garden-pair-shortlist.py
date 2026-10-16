#!/usr/bin/env python3
"""PlotNua · The Borrowed Garden · POSSIBLE-PAIR SHORTLIST (founder-only, offline).

Reads two CSV exports the founder makes from the private register base
(Gardens and Growers) and writes a shortlist of POSSIBLE pairs for the
founder to consider. It is a reading aid, not a matcher:

  * it contacts nobody, writes nothing to Airtable and has no network code;
  * it never prints or writes a name, an email address or a note: pairs are
    identified by record_ref only (an Airtable RECORD_ID() formula column);
  * a pair on the shortlist is NOT an introduction and NOT a decision. Any
    introduction stays founder-controlled and consent-based (G1B §6–§7), and
    G7 (the first real introduction) remains BLOCKED until the insurance
    question is resolved.

Usage:
  python3 atlas-tools/borrowed-garden-pair-shortlist.py Gardens.csv Growers.csv [-o shortlist.csv]

FRAMEWORK (v1, deliberately small for the pilot):
  Gates, either side (a record failing a gate is listed as "not considered" with
  the reason, never silently dropped):
    - status is not paused / withdrawn
    - district is one of the four pilot districts
  Garden-only gates (G1B §5 tenure rule, unchanged):
    - own: ok · rent: only with permission_confirmed AND a statement of 20+ chars
    - buying or absent: not considered (stored, never put forward)
  Fit tests for a garden x grower pair:
    - distance: approximate district-centre distance <= the grower's travel radius
    - space: garden size band >= the size the grower wants
    - timing: equal, or either flexible, or this_season ~ within_3_months
  Flags (do not exclude; prompt a conversation):
    - water none or not_sure · either side's size not_sure
    - garden note or grower note present (read it before deciding)
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

PILOT = ["raheny", "killester", "donnycarney", "artane"]
# Approximate distances between district centres, km (straight line, rounded
# up). Same district: 1 km. A planning aid only; never shown to anyone else.
KM = {
    frozenset(["raheny", "killester"]): 2.5, frozenset(["raheny", "artane"]): 3.0,
    frozenset(["raheny", "donnycarney"]): 3.5, frozenset(["killester", "donnycarney"]): 1.5,
    frozenset(["killester", "artane"]): 2.0, frozenset(["donnycarney", "artane"]): 1.5,
}
# Grower travel (16 Oct 2026 refinement). Blank = not given: same district only, flagged.
RADIUS_KM = {"up_to_5km": 5.0, "up_to_10km": 10.0, "up_to_20km": 20.0, "more_than_20km": 50.0, "flexible": 50.0,
             "": 1.0}
SIZE = ["very_small", "small", "medium", "large"]
NEAR_TIMING = {frozenset(["this_season", "within_3_months"])}
NOT_ACTIVE = {"paused", "withdrawn"}
# Columns the tool reads. Anything else in the export (names, emails, notes'
# text) is never copied to the output.
GARDEN_COLS = ["record_ref", "status", "district", "size_note", "water", "timing", "inherited_tenure",
               "permission_confirmed", "garden_note"]
GROWER_COLS = ["record_ref", "status", "county", "district", "travel_distance", "space_wanted", "timing", "growing_note"]


def km(a: str, b: str) -> float:
    return 1.0 if a == b else KM.get(frozenset([a, b]), 99.0)


def truthy(v: str) -> bool:
    return str(v).strip().lower() in {"true", "checked", "yes", "1", "x"}


def load(path: Path, cols: list[str], prefix: str) -> list[dict]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        rows = list(csv.DictReader(f))
    out = []
    for i, r in enumerate(rows, 1):
        d = {c: (r.get(c) or "").strip() for c in cols}
        if not d["record_ref"]:
            d["record_ref"] = f"{prefix}-row{i}"
        out.append(d)
    return out


def garden_gate(g: dict) -> str | None:
    if g["status"] in NOT_ACTIVE:
        return f"status {g['status']}"
    if g["district"] not in PILOT:
        return "outside the four pilot districts"
    t = g["inherited_tenure"]
    if t == "own":
        return None
    if t == "rent":
        if truthy(g["permission_confirmed"]) and len(g["garden_note"]) >= 20:
            return None
        return "renting without both the permission tick and a statement (G1B §5)"
    return f"tenure '{t or 'absent'}' is never put forward (G1B §5)"


def grower_gate(p: dict) -> str | None:
    if p["status"] in NOT_ACTIVE:
        return f"status {p['status']}"
    if p["district"] not in PILOT:
        return "outside the four pilot districts"
    return None


def assess(g: dict, p: dict):
    reasons, flags = [], []
    d = km(g["district"], p["district"])
    radius = RADIUS_KM.get(p["travel_distance"], 0)
    if d > radius:
        return None
    if p["travel_distance"]:
        reasons.append(f"~{d:g} km apart, within the grower's {p['travel_distance'].replace('_', ' ')}")
    else:
        reasons.append("same district (grower did not say how far they'd travel)")
    gs, ps = g["size_note"], p["space_wanted"]
    if "not_sure" in (gs, ps):
        flags.append("size not sure on one side")
    elif SIZE.index(gs) < SIZE.index(ps):
        return None
    else:
        reasons.append(f"garden {gs.replace('_', ' ')} >= wanted {ps.replace('_', ' ')}")
    gt, pt = g["timing"], p["timing"]
    if gt == pt or "flexible" in (gt, pt) or frozenset([gt, pt]) in NEAR_TIMING:
        reasons.append(f"timing compatible ({gt} / {pt})")
    else:
        return None
    if g["water"] in ("none", "not_sure"):
        flags.append(f"water: {g['water']}")
    if g["garden_note"]:
        flags.append("read the garden note")
    if p["growing_note"]:
        flags.append("read the grower note")
    if not p["travel_distance"]:
        flags.append("grower travel not given")
    score = (radius - d) + (0 if flags else 1) + (1 if gt == pt else 0)
    return d, score, reasons, flags


def shortlist(gardens: list[dict], growers: list[dict]):
    pairs, excluded = [], []
    ok_g = []
    for g in gardens:
        why = garden_gate(g)
        (excluded.append(("garden", g["record_ref"], why)) if why else ok_g.append(g))
    ok_p = []
    for p in growers:
        why = grower_gate(p)
        (excluded.append(("grower", p["record_ref"], why)) if why else ok_p.append(p))
    for g in ok_g:
        for p in ok_p:
            r = assess(g, p)
            if r:
                d, score, reasons, flags = r
                pairs.append({"garden_ref": g["record_ref"], "grower_ref": p["record_ref"], "approx_km": d,
                              "why": "; ".join(reasons), "flags": "; ".join(flags), "score": round(score, 2)})
    pairs.sort(key=lambda x: (-x["score"], x["approx_km"], x["garden_ref"], x["grower_ref"]))
    return pairs, excluded


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("gardens")
    ap.add_argument("growers")
    ap.add_argument("-o", "--out", default="possible-pairs.csv")
    a = ap.parse_args(argv)
    pairs, excluded = shortlist(load(Path(a.gardens), GARDEN_COLS, "G"), load(Path(a.growers), GROWER_COLS, "P"))
    with open(a.out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["garden_ref", "grower_ref", "approx_km", "score", "why", "flags", "status"])
        w.writeheader()
        for p in pairs:
            w.writerow({**p, "status": "possible - founder review; nobody contacted"})
    print(f"{len(pairs)} possible pair(s) -> {a.out}. Nobody has been contacted.")
    for side, ref, why in excluded:
        print(f"  not considered: {side} {ref} - {why}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
