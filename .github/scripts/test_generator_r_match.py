#!/usr/bin/env python3
"""
STAGE 3D-D2 — R-MATCH IN THE REAL GENERATOR, OFFLINE (founder approval 7 Nov 2026).

Runs generate_garden_room_universe.py through its own --snapshot switch against an
Airtable-shaped snapshot rebuilt from the published universe for a fixed set of
real products, at chosen --price-as-of dates. No token, no network, no Airtable;
the production VAT register is replaced by an empty fixture so no register product
is needed, and the production hold register is read, never written.

    R1  a Verified, dated, product-specific euro price        -> eligible, fresh until check + 180
    R2  Sprout Pod: Partially Verified, undated, Range-Level  -> not-verified, never matching
    R3  Elm: Partially Verified, dated                        -> not-verified
    R4  Zomes: Partially Verified USD                         -> not-verified (never euro anyway)
    R5  a Verified GBP Range-Level price                      -> not-verified (rule 7)
    R6  NOOK and Rayco (presentation holds)                   -> held, no expiry, never matching
    R7  expiry boundary: eligible ON priceFreshUntil, not-verified the day after
    R8  a check date in the future                            -> not eligible
    R9  an unaccepted Price Type (Custom Quote)               -> not-verified

Run:  python3 .github/scripts/test_generator_r_match.py
"""
import datetime as dt, json, os, subprocess, sys, tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
GEN = HERE / "generate_garden_room_universe.py"
U = {p["id"]: p for p in json.loads((ROOT / "garden-room-recommendation-universe-v1.json").read_text())["products"]}
PASS = FAIL = 0


def ck(label, cond, detail=None):
    global PASS, FAIL
    if cond:
        PASS += 1; print(f"    ok   {label}")
    else:
        FAIL += 1; print(f"    *** FAIL *** {label}" + (f"  {detail!r}" if detail is not None else ""))


def pick(pred):
    return next(p["id"] for p in U.values() if pred(p))


ref = lambda p: p.get("priceEvidenceRef") or {}
held = lambda p: bool((p.get("priceEvidence") or {}).get("presentationHold"))
VER = pick(lambda p: p.get("priceStatus") == "Verified" and p.get("currency") == "EUR" and not held(p)
           and p["organisation"] not in ("Hansa24 Group",) and p.get("priceScope") == "Product-Specific"
           and ref(p).get("lastPriceCheck") == "2026-11-06" and ref(p).get("candidateCount") == 1)
SPROUT = "recToZjhvh3r0TiFa"
ELM = pick(lambda p: p["organisation"].startswith("Elm") and p.get("priceStatus") == "Partially Verified")
ZOMES = pick(lambda p: p.get("currency") == "USD")
QUINN = "recBNvHGTweLtP11Q"
NOOK, RAYCO = "recDa5vihxcYG9xoH", "recDIcUb7S6pP8JCx"
FIX = [VER, SPROUT, ELM, ZOMES, QUINN, NOOK, RAYCO]


def snapshot(override=None):
    orgs, products, pricing = {}, [], []
    for pid in FIX:
        p = U[pid]
        oid = orgs.setdefault(p["organisation"], "recORGRM%09d" % len(orgs))
        products.append({"id": pid, "fields": {"Product Name": p["name"], "Product Category": "Garden Rooms",
                         "Product Code": pid, "Status": "Active", "Verification Status": "Verified",
                         "Product URL": p.get("productUrl") or "https://example.ie/" + pid,
                         "Organisation": [{"id": oid}]}})
        pe, r = p["priceEvidence"], ref(p)
        f = {"Product": [{"id": pid}], "Base Price": pe.get("base"), "Currency": pe.get("currency"),
             "Price Type": pe.get("priceType"), "Status": pe.get("status"), "Evidence Scope": pe.get("evidenceScope") or p.get("priceScope"),
             "Last Price Check": r.get("lastPriceCheck"), "Price Includes VAT": pe.get("includesVat"),
             "Price From": pe.get("from"), "Price To": pe.get("to")}
        f.update((override or {}).get(pid, {}))
        pricing.append({"id": r["recordIds"][0], "fields": {k: v for k, v in f.items() if v is not None}})
    return {"products": products, "pricing": pricing, "availability": [], "featureValues": [], "features": [],
            "organisations": [{"id": oid, "fields": {"Organisation Name": n, "Organisation Type": "Manufacturer",
                                                     "Website": "https://example.ie/"}} for n, oid in orgs.items()]}


def run(as_of, snap):
    with tempfile.TemporaryDirectory() as t:
        t = Path(t)
        (t / "s.json").write_text(json.dumps(snap))
        (t / "reg.json").write_text(json.dumps({"schema": "plotnua.vat-terms-evidence", "version": 1, "suppliers": []}))
        env = dict(os.environ, PYTHONPATH=str(HERE))
        r = subprocess.run([sys.executable, str(GEN), "--out-dir", str(t / "out"), "--snapshot", str(t / "s.json"),
                            "--vat-terms-register", str(t / "reg.json"), "--price-as-of", as_of],
                           capture_output=True, text=True, env=env)
        f = t / "out" / "garden-room-recommendation-universe-v1.json"
        return r, ({p["id"]: p for p in json.loads(f.read_text())["products"]} if f.exists() else None)


print("STAGE 3D-D2 — R-MATCH in the real generator (offline)")
r, g = run("2026-11-07", snapshot())
ck("generator runs", r.returncode == 0 and g, (r.stdout + r.stderr)[-500:])
if g:
    v = g[VER]
    until = (dt.date.fromisoformat(ref(U[VER])["lastPriceCheck"]) + dt.timedelta(days=180)).isoformat()
    ck("R1 Verified dated euro price is eligible, fresh until check + 180", v["priceSafeForMatching"] is True
       and v["priceState"] == "eligible" and v["priceFreshUntil"] == until, (v.get("priceState"), v.get("priceFreshUntil")))
    for name, pid in (("R2 Sprout Pod (PV, undated, Range-Level)", SPROUT), ("R3 Elm (PV, dated)", ELM),
                      ("R4 Zomes (PV, USD)", ZOMES), ("R5 GBP Verified Range-Level", QUINN)):
        x = g[pid]
        ck(name + " is not-verified, never matching", x["priceSafeForMatching"] is False and x["priceState"] == "not-verified"
           and x["priceFreshUntil"] is None and x["price"] == U[pid]["price"], (x.get("priceState"), x.get("price")))
    for name, pid in (("R6 NOOK", NOOK), ("R6 Rayco", RAYCO)):
        x = g[pid]
        ck(name + " is held, no expiry, never matching, price kept in data",
           x["priceState"] == "held" and x["priceSafeForMatching"] is False and x["priceFreshUntil"] is None
           and x["price"] == U[pid]["price"], (x.get("priceState"),))
    ck("the run reports its R-MATCH date", "R-MATCH as of 2026-11-07" in r.stdout)
r, g = run(until, snapshot())
ck("R7 eligible ON its priceFreshUntil (%s)" % until, g and g[VER]["priceState"] == "eligible", g and g[VER]["priceState"])
nxt = (dt.date.fromisoformat(until) + dt.timedelta(days=1)).isoformat()
r, g = run(nxt, snapshot())
ck("R7 not-verified the day after (%s)" % nxt, g and g[VER]["priceState"] == "not-verified"
   and g[VER]["priceSafeForMatching"] is False and g[VER]["priceFreshUntil"] is None, g and g[VER]["priceState"])
r, g = run("2026-11-07", snapshot({VER: {"Last Price Check": "2026-12-01"}}))
ck("R8 a future check date is not eligible", g and g[VER]["priceState"] == "not-verified", g and g[VER]["priceState"])
r, g = run("2026-11-07", snapshot({VER: {"Price Type": "Custom Quote"}}))
ck("R9 an unaccepted Price Type is not eligible", g and g[VER]["priceState"] == "not-verified", g and g[VER]["priceState"])
print("\n" + "=" * 78 + f"\n  {PASS} passed, {FAIL} failed\n" + "=" * 78)
sys.exit(1 if FAIL else 0)
