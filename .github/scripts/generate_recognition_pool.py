#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Regenerate atlas-recognition-pool.json — the canonical Atlas product catalogue
the manual-add resolver searches for PRODUCT IDENTITY.

WHY THIS SCRIPT HAD TO EXIST.
    The shipped atlas-recognition-pool.json is an export of 516 Products taken
    on 27 August 2026. Atlas held 1,187 Products when this was written, and the
    shipped export contains ZERO records for at least one organisation whose
    products the site already displays. A homeowner typing the name of a real
    Atlas product was told PlotNua had no record of it — not because the
    resolver was wrong, but because the file it searches had gone stale and
    nothing in the repository could refresh it. Every other Atlas-derived
    artefact has a generator; this one did not.

IDENTITY IS NOT ELIGIBILITY.
    This export answers "does Atlas know this product?" and nothing else. It
    deliberately carries NO price, NO area, NO evidence and NO ranking input,
    so it can never become a second source of truth for the recommendation
    universe. Whether a product is recommendABLE is decided by
    generate_garden_room_universe.py and is a separate question.

    For the same reason there is NO product-type filter and NO exclusion list.
    A product Atlas holds is a product Atlas knows, whatever its category — a
    sauna is not a garden room, but Atlas still knows the sauna, and telling a
    homeowner otherwise is the defect this file exists to prevent.

WHAT IT WRITES — exactly the six keys the runtime reads, and no more:
    id, name, organisation, url, status, verification

NO WRITES OF ANY KIND TO AIRTABLE. Read-only, GET only, like every other
generator here. The token is read from the environment and never logged.

Run:
    AIRTABLE_TOKEN=... python3 .github/scripts/generate_recognition_pool.py \
        --out atlas-recognition-pool.json
    python3 .github/scripts/generate_recognition_pool.py --verify-only
"""

import argparse
import json
import os
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from atlas_common import fetch_all, cell, links, txt, fail   # noqa: E402

PRODUCTS = "tblMiUcO4OT9ia2aE"

FIELDS = ["Product Name", "Organisation", "Product URL", "Status",
          "Verification Status"]

# The runtime reads exactly these. A key added here is a key shipped to every
# browser, so the list is explicit rather than "whatever Airtable returned".
KEYS = ("id", "name", "organisation", "url", "status", "verification")

# A refresh that collapses the catalogue is far more likely to be a broken read
# than a genuinely emptied Atlas, so it fails rather than publishes.
MIN_RECORDS = 400


def build(raw, org_names):
    out = []
    for rec in raw:
        name = txt(cell(rec, "Product Name")) or ""
        if not name.strip():
            continue          # a product with no name cannot be identified
        org_ids = links(rec, "Organisation")
        org = org_names.get(org_ids[0], "") if org_ids else ""
        out.append({
            "id": rec.get("id"),
            "name": name,
            "organisation": org,
            "url": txt(cell(rec, "Product URL")) or None,
            "status": txt(cell(rec, "Status")) or None,
            "verification": txt(cell(rec, "Verification Status")) or None,
        })
    out.sort(key=lambda r: r["id"] or "")
    return out


def validate(rows, previous=None):
    """Every claim this file makes about itself, checked before it ships."""
    problems = []

    if len(rows) < MIN_RECORDS:
        problems.append("only %d record(s); a catalogue this small is far more "
                        "likely to be a broken read than a real Atlas"
                        % len(rows))

    ids = [r["id"] for r in rows]
    if len(set(ids)) != len(ids):
        problems.append("duplicate product ids: a product resolving to two "
                        "records is the exact failure this file prevents")
    bad = [i for i in ids if not (isinstance(i, str) and i.startswith("rec")
                                  and len(i) == 17)]
    if bad:
        problems.append("%d malformed product id(s), e.g. %r" % (len(bad), bad[0]))

    for r in rows:
        extra = set(r) - set(KEYS)
        if extra:
            problems.append("record %s carries unexpected key(s) %s — this "
                            "export must stay identity-only"
                            % (r["id"], sorted(extra)))
            break

    unnamed = [r["id"] for r in rows if not r["name"].strip()]
    if unnamed:
        problems.append("%d record(s) with no name" % len(unnamed))

    noorg = sum(1 for r in rows if not r["organisation"])
    # Not fatal: Atlas genuinely holds products whose organisation link is not
    # yet made. It IS reported, because a sudden jump means the link field was
    # misread rather than that Atlas changed.
    print("  records with no organisation: %d" % noorg)

    if previous is not None:
        lost = set(p["id"] for p in previous) - set(ids)
        if len(lost) > len(previous) * 0.10:
            problems.append("%d of %d previously-known products are absent; a "
                            "refresh that drops a tenth of the catalogue is "
                            "refused" % (len(lost), len(previous)))

    return problems


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="atlas-recognition-pool.json")
    ap.add_argument("--snapshot", default=None,
                    help="Read a saved Airtable response instead of the network.")
    ap.add_argument("--write-snapshot", default=None)
    ap.add_argument("--verify-only", action="store_true",
                    help="Validate the file already on disk and write nothing.")
    args = ap.parse_args()

    out_path = pathlib.Path(args.out)
    previous = None
    if out_path.exists():
        try:
            previous = json.loads(out_path.read_text(encoding="utf-8"))
        except Exception:
            previous = None

    if args.verify_only:
        if previous is None:
            fail("--verify-only: %s is missing or unreadable" % out_path)
        print("Verifying %s (%d records)" % (out_path, len(previous)))
        problems = validate(previous)
        for p in problems:
            print("  FAIL  " + p)
        if problems:
            fail("%d problem(s)" % len(problems))
        print("\nVERIFY PASS")
        return

    if args.snapshot:
        snap = json.loads(pathlib.Path(args.snapshot).read_text(encoding="utf-8"))
        raw, orgs_raw = snap["products"], snap["organisations"]
    else:
        token = os.environ.get("AIRTABLE_TOKEN")
        if not token:
            fail("AIRTABLE_TOKEN is not set. This script reads Atlas directly; "
                 "it does not guess and it does not carry a fallback dataset.")
        print("Reading Atlas (GET only)…")
        raw = fetch_all(token, PRODUCTS, FIELDS)
        org_ids = set()
        for rec in raw:
            org_ids.update(links(rec, "Organisation"))
        orgs_raw = fetch_all(token, "tblngwmviAcWxFKsW", ["Organisation Name"])
        orgs_raw = [o for o in orgs_raw if o.get("id") in org_ids]

    if args.write_snapshot:
        pathlib.Path(args.write_snapshot).write_text(
            json.dumps({"products": raw, "organisations": orgs_raw}, indent=1),
            encoding="utf-8")

    org_names = {}
    for o in orgs_raw:
        org_names[o.get("id")] = txt(cell(o, "Organisation Name")) or ""

    rows = build(raw, org_names)
    print("  products read:        %d" % len(raw))
    print("  products exported:    %d" % len(rows))
    print("  organisations named:  %d" % len(set(r["organisation"] for r in rows if r["organisation"])))
    if previous:
        print("  previous export:      %d" % len(previous))
        print("  newly known:          %d"
              % len(set(r["id"] for r in rows) - set(p["id"] for p in previous)))

    problems = validate(rows, previous)
    for p in problems:
        print("  FAIL  " + p)
    if problems:
        fail("%d problem(s); nothing written" % len(problems))

    out_path.write_text(json.dumps(rows, ensure_ascii=False, indent=1) + "\n",
                        encoding="utf-8")
    print("\nwritten: %s" % out_path)


if __name__ == "__main__":
    main()
