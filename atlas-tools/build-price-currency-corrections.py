#!/usr/bin/env python3
"""
PRICE CURRENCY CORRECTIONS — apply atlas-tools/price-currency-corrections.json
to the published wellness-universe-v1.json.
===============================================================================
AUTHORITY. Founder review, 22 October 2026, 16:26 Dublin ("TimberIN final
coordinated release — final correction"): TimberIN publishes its prices in
GBP while PlotNua showed the same numbers as EUR. "Correct this before
deployment. Preserve verified GBP prices. Do not invent EUR conversions. Do
not assume VAT treatment. Preserve existing price provenance. Do not modify
Airtable."

WHY THIS TOOL EXISTS. The universe is generated from a frozen Atlas snapshot
that is never committed, and Atlas must not be modified, so the universe
cannot simply be regenerated. The generator now applies the register itself
(so any future regeneration or targeted update carries the correction); this
tool applies the SAME function, corrected_price(), to the six published
records in place, and nothing else.

WHAT CHANGES, PER LISTED RECORD: price.currency EUR -> GBP, and the price
basis gains ", in pounds sterling as the supplier publishes it". The amount,
the price type, the VAT sentence, the state and every other field and record
stay byte-for-byte.

GUARDS (every mode)
  C1 the register is well formed; every correction names a public TimberIN
     record of this universe whose product URL is the evidenced URL
  C2 the Atlas amount and type equal the evidenced amount and type
  C3 after applying: exactly the listed records differ, and only in
     price.currency and price.basis; amounts and VAT sentences unchanged
  C4 the file serialises exactly as the generator writes it
  C5 the published Discovery snapshot (atlas-tools/discovery-maker-snapshot-v1.json)
     changes only in the six records' price line, to exactly what the maker
     directory renders from the corrected universe

    python3 atlas-tools/build-price-currency-corrections.py --check   # verify: applied and consistent
    python3 atlas-tools/build-price-currency-corrections.py --apply   # apply (idempotent)
"""
import importlib.util
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
UNI = ROOT / "wellness-universe-v1.json"
spec = importlib.util.spec_from_file_location("gw", ROOT / ".github/scripts/generate_wellness_universe.py")
GW = importlib.util.module_from_spec(spec)
sys.path.insert(0, str(ROOT / ".github/scripts"))
spec.loader.exec_module(GW)


SNAP = ROOT / "atlas-tools" / "discovery-maker-snapshot-v1.json"
mspec = importlib.util.spec_from_file_location("mx", ROOT / "atlas-tools/build-maker-explorer.py")
MX = importlib.util.module_from_spec(mspec)
mspec.loader.exec_module(MX)


def sdump(d):
    return json.dumps(d, indent=1, ensure_ascii=False, sort_keys=True) + "\n"


def die(msg):
    print("REFUSED: " + msg)
    sys.exit(1)


def dump(d):
    return json.dumps(d, ensure_ascii=False, indent=2) + "\n"


def main():
    mode = (sys.argv[1:] or ["--check"])[0]
    if mode not in ("--check", "--apply"):
        die("say --check or --apply")
    raw = UNI.read_text(encoding="utf-8")
    U = json.loads(raw)
    if dump(U) != raw:
        die("C4 the universe does not serialise as the generator writes it")
    corr = GW.currency_corrections()
    if not corr:
        die("C1 the register is empty or missing")
    by = {r["id"]: r for r in U["products"]}
    for pid, c in corr.items():
        r = by.get(pid)
        if not r:
            die("C1 %s is not in the wellness universe" % pid)
        if r["organisation"] != c["organisation"] or r["productUrl"] != c["productUrl"] \
                or r["productName"] != c["productName"]:
            die("C1 %s does not match its register entry (organisation, name or URL)" % pid)
        if r["publicVisibility"] != "PUBLISHABLE" or r["qualification"]["state"] != "ELIGIBLE":
            die("C1 %s is not a public record" % pid)
        ev = c.get("evidence") or {}
        sd = ev.get("structuredData") or {}
        if ev.get("httpStatus") != 200 or ev.get("finalUrl") != c["productUrl"] \
                or sd.get("offerPriceCurrency") != c["publishedCurrency"] or str(c["amount"]) != sd.get("offerPrice"):
            die("C1 %s evidence does not support the correction" % pid)
    new = json.loads(raw)
    for r in new["products"]:
        if r["id"] in corr:
            r["price"] = GW.corrected_price(r["id"], r["price"], corr)   # C2 enforced inside
    # C3
    for a, b in zip(U["products"], new["products"]):
        if a["id"] in corr:
            pa, pb = a["price"], b["price"]
            if {k: v for k, v in pa.items() if k not in ("currency", "basis")} != \
               {k: v for k, v in pb.items() if k not in ("currency", "basis")}:
                die("C3 %s changed beyond currency and basis" % a["id"])
            if pb["currency"] != corr[a["id"]]["publishedCurrency"]:
                die("C3 %s currency not corrected" % a["id"])
            if not pb["basis"].endswith(pa["basis"].split(".", 1)[1] if "." in pa["basis"] else ""):
                die("C3 %s VAT sentence changed" % a["id"])
            if {k: v for k, v in a.items() if k != "price"} != {k: v for k, v in b.items() if k != "price"}:
                die("C3 %s changed outside its price" % a["id"])
        elif a != b:
            die("C3 %s is not in the register but would change" % a["id"])
    if {k: v for k, v in U.items() if k != "products"} != {k: v for k, v in new.items() if k != "products"}:
        die("C3 the universe envelope would change")
    out = dump(new)
    # C5 the published Discovery snapshot (served at atlas-tools/...) carries, for
    # these records only, the price line the maker directory renders from the
    # corrected universe; every other byte of it is unchanged.
    snap_raw = SNAP.read_text(encoding="utf-8")
    S = json.loads(snap_raw)
    if sdump(S) != snap_raw: die("C5 the Discovery snapshot does not serialise as sync-discovery-makers writes it")
    S2 = json.loads(snap_raw)
    for r in new["products"]:
        if r["id"] in corr:
            e = S2["products"].get(r["id"])
            if not e or e.get("source") != "wellness-universe-v1": die("C5 %s missing from the Discovery snapshot" % r["id"])
            e["price"] = MX.price_line(r["price"])
            if not e["price"].startswith(("£", "From £")): die("C5 %s would not render in GBP" % r["id"])
    for k in S["products"]:
        if k not in corr and S["products"][k] != S2["products"][k]: die("C5 %s would change" % k)
    if {k: v for k, v in S.items() if k != "products"} != {k: v for k, v in S2.items() if k != "products"}:
        die("C5 the snapshot envelope would change")
    sout = sdump(S2)
    if mode == "--check":
        if out != raw:
            die("the register is not applied to wellness-universe-v1.json; run --apply")
        if sout != snap_raw:
            die("the register is not applied to the Discovery snapshot; run --apply")
        print("CHECK OK — %d register record(s) carry the supplier's published currency in the universe and the "
              "Discovery snapshot; nothing else differs" % len(corr))
        return
    if out == raw and sout == snap_raw:
        print("APPLY: already applied (no change)")
        return
    UNI.write_text(out, encoding="utf-8")
    SNAP.write_text(sout, encoding="utf-8")
    print("APPLIED to %d record(s): universe currency and basis, snapshot price line; nothing else" % len(corr))


if __name__ == "__main__":
    main()
