#!/usr/bin/env python3
"""PlotNua — test_additional_home_stats.py

REGRESSION TEST for the Stage 3 generator crash of 11 October 2026:

    TypeError: '<' not supported between instances of 'NoneType' and 'NoneType'
    generate_additional_home_universe.py  "categoryWithoutConfirmed"

An Additional Home product with NO Product Code reaches the statistics as
`productCode: None`, because the record writes `txt(...) or None` and
"Product Code" is requested but NOT required by the snapshot. TWO of them made
sorted() compare None with None. One would not have: a one-element sort
compares nothing, which is why this sat latent until a second uncoded product
was created.

The real snapshot had exactly two, both Yardbox, both created 29 September:
Aspect Modular Homes and Bothán. This test reproduces that shape -- two
uncoded, habitation-unconfirmed Additional Home products -- and drives THE
REAL GENERATOR as a subprocess against it.

T5 is the part that makes the rest mean anything: it rebuilds the PRE-FIX
expression and asserts it still raises TypeError on this data. A regression
test that cannot reproduce the original failure proves nothing.

No network. No token. Writes only to a temporary directory.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
GEN = HERE / "generate_additional_home_universe.py"
AH = "Additional Home"
CONFIRMED = "CONFIRMED RESIDENTIAL HABITATION"

PASS, FAIL = [], []


def check(name, ok, detail=""):
    (PASS if ok else FAIL).append(name)
    print(f"  {'PASS' if ok else 'FAIL'}  {name}")
    if detail:
        print(f"        {detail}")


def product(rid, name, code, habitation, org="recORG", slug="x"):
    """One products-table record, in snapshot shape.

    NOTE the Product URL carries a SLUG, not the record id. The first draft of
    this fixture put `rid` in the URL and the generator's public-disclosure
    firewall rejected the whole run — "raw record id at .products[0].productUrl".
    That is the firewall doing its job, and it is the same reason the fix names
    uncoded products by product name rather than by record id."""
    f = {"Product Name": name, "Product Category": AH,
         "Organisation": [org],
         "Habitation Classification Basis": "Test fixture. No governed prose.",
         "Product URL": "https://example.invalid/" + slug}
    if code:
        f["Product Code"] = code
    if habitation:
        f["Habitation Classification"] = habitation
    return {"id": rid, "fields": f}


def snapshot():
    """Two uncoded unconfirmed products -- the crash shape -- plus one normal
    coded product, so the test also proves the coded list still works."""
    return {
        "products": [
            # The two real offenders, by name, uncoded and unconfirmed.
            product("recFek9ErsnKt6uKN", "Yardbox Aspect Modular Homes",
                    None, None, slug="aspect"),
            product("recPermX1OwzI2o1Y", "Yardbox Bothán", None, None,
                    slug="bothan"),
            # A coded, unconfirmed product: belongs in the coded list.
            product("recCODED00000001", "Coded But Unconfirmed",
                    "PROD-000001", "PROBABLE — MORE EVIDENCE REQUIRED",
                    slug="coded-unconfirmed"),
            # A coded, CONFIRMED product: belongs in neither list.
            product("recCODED00000002", "Coded And Confirmed",
                    "PROD-000002", CONFIRMED, slug="coded-confirmed"),
        ],
        "pricing": [],
        "availability": [],
        "featureValues": [],
        "features": [],
        "organisations": [
            {"id": "recORG", "fields": {"Organisation Name": "Test Supplier"}}
        ],
        "sources": [],
    }


def main() -> int:
    print("\n  ADDITIONAL HOME STATISTICS — REGRESSION (uncoded products)")
    print("  " + "-" * 68)

    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        snap = tmp / "snapshot.json"
        snap.write_text(json.dumps(snapshot()), encoding="utf-8")
        out = tmp / "out"
        out.mkdir()

        proc = subprocess.run(
            [sys.executable, str(GEN), "--snapshot", str(snap),
             "--out-dir", str(out)],
            capture_output=True, text=True)

        # T1 — the generator completes. This is the regression itself.
        check("T1  the generator survives two uncoded products",
              proc.returncode == 0,
              f"exit {proc.returncode}"
              + (f" · {proc.stderr.strip().splitlines()[-1]}"
                 if proc.returncode and proc.stderr.strip() else ""))
        if proc.returncode != 0:
            print("\n  the generator failed, so the remaining checks cannot run.\n")
            return 1

        payload = json.loads(
            (out / "additional-home-universe-v1.json").read_text(encoding="utf-8"))

        # T2 — the coded unconfirmed product is listed, by code.
        cwc = payload.get("categoryWithoutConfirmed")
        check("T2  coded unconfirmed products are listed by code",
              cwc == ["PROD-000001"], f"{cwc!r}")

        # T3 — no None, and no invented placeholder, leaked into that list.
        bad = [c for c in (cwc or []) if not isinstance(c, str) or not c.strip()]
        check("T3  the code list carries no null and no empty placeholder",
              bad == [], f"offending entries: {bad!r}")

        # T4 — the uncoded products are NOT discarded. They are named.
        unc = payload.get("categoryWithoutConfirmedUncoded")
        check("T4  uncoded products are preserved, by product name",
              unc == ["Yardbox Aspect Modular Homes", "Yardbox Bothán"],
              f"{unc!r}")

        # T4b — and named by GOVERNED data, never by record id. A record id
        # here would also trip the generator's own firewall.
        import re
        leaked = [u for u in (unc or [])
                  if re.search(r"\brec[A-Za-z0-9]{14}\b", u)]
        check("T4b uncoded products are not identified by Airtable record id",
              leaked == [], f"leaked: {leaked!r}")

        # T5 — THE CAPABILITY PROOF. Rebuild the pre-fix expression over the
        # same emitted records and assert it STILL raises. Without this, T1
        # could be passing for some unrelated reason.
        emitted = payload["products"]
        try:
            sorted(r["productCode"] for r in emitted
                   if r["habitation"]["state"] != CONFIRMED)
            check("T5  the PRE-FIX expression still raises on this data",
                  False, "it did not raise — the fixture no longer reproduces "
                         "the bug, so T1 proves nothing")
        except TypeError as e:
            check("T5  the PRE-FIX expression still raises on this data",
                  "NoneType" in str(e), str(e))

        # T6 — one uncoded product alone must NOT have crashed the old code.
        # This is why the bug was latent, and it is worth pinning so nobody
        # "fixes" a single-None case and assumes they have covered this.
        one = [r for r in emitted if r["productCode"] is None][:1]
        try:
            sorted(r["productCode"] for r in one)
            check("T6  a single uncoded product never tripped the old sort",
                  True, "confirms why this stayed latent until the second one")
        except TypeError as e:
            check("T6  a single uncoded product never tripped the old sort",
                  False, f"unexpectedly raised: {e}")

        # T7 — the confirmed product appears in neither gap list.
        check("T7  a confirmed, coded product is in neither gap list",
              "PROD-000002" not in (cwc or [])
              and "Coded And Confirmed" not in (unc or []),
              "the statistic still means what its name says")

        # T8 — nothing else about the artefact shifted: the gate is declared
        # and the counts are self-consistent.
        gate = (payload.get("publicationGate") or {}).get("version")
        check("T8  the publication gate is still declared",
              gate == "supplier-publication-gate-v1", f"{gate!r}")
        check("T9  confirmedHabitationCount matches the fixture",
              payload.get("confirmedHabitationCount") == 1,
              f"{payload.get('confirmedHabitationCount')!r}")

    print("  " + "-" * 68)
    print(f"  {len(PASS) + len(FAIL)} checks, {len(PASS)} passed, "
          f"{len(FAIL)} failed\n")
    return 1 if FAIL else 0


if __name__ == "__main__":
    sys.exit(main())
