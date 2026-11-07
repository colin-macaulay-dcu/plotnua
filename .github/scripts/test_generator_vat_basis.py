#!/usr/bin/env python3
"""
STAGE 3D-D1 — THE SUPPLIER-TERMS VAT BASIS SURVIVES A FULL REGENERATION.

Runs the REAL generator, offline, through its own --snapshot switch, against
an Airtable-shaped snapshot rebuilt from the published universe: every product
the VAT terms register names (with its real product id, organisation and
adjudicated price record), two Hansa24 products the register does NOT name
(one of them with VAT = Yes stated on its own page), and two products from
other suppliers. No token, no network, no Airtable. The production register is
READ, never written: every refusal case runs against a mutated COPY in a
temporary directory.

    G1  the real register + a faithful snapshot  -> exactly the register's
        products carry vatBasis "supplier-terms", with the published price
        evidence; nothing is inferred for any other product
    N1  register expired                          -> regeneration refused
    N2  wrong organisation in Atlas               -> refused
    N3  register names the wrong product          -> refused
    N4  adjudicated price record not the one checked -> refused
    N5  Atlas VAT is not Yes                       -> refused
    N6  register product absent from Atlas         -> refused
    N7  register schema invalid / duplicate entry  -> refused
    N8  register missing                           -> refused
In every refusal no universe is written.

Run:  python3 .github/scripts/test_generator_vat_basis.py [--universe PATH]
"""
import copy, datetime as dt, json, os, subprocess, sys, tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
GEN = HERE / "generate_garden_room_universe.py"
REGISTER = ROOT / "atlas-tools" / "vat-terms-evidence.json"
UNIVERSE = Path(sys.argv[sys.argv.index("--universe") + 1]) if "--universe" in sys.argv \
    else ROOT / "garden-room-recommendation-universe-v1.json"
OUTFILE = "garden-room-recommendation-universe-v1.json"
PASS = FAIL = 0


def ck(label, cond, detail=None):
    global PASS, FAIL
    if cond:
        PASS += 1
        print(f"    ok   {label}")
    else:
        FAIL += 1
        print(f"    *** FAIL *** {label}" + (f"  {detail!r}" if detail is not None else ""))


def rec(rid, fields):
    return {"id": rid, "fields": fields}


REG = json.loads(REGISTER.read_text(encoding="utf-8"))
U = {p["id"]: p for p in json.loads(UNIVERSE.read_text(encoding="utf-8"))["products"]}
REG_PIDS = [x["productId"] for e in REG["suppliers"] if e["status"] == "accepted"
            for x in e["productPagesChecked"]]
H = "Hansa24 Group"
UNNAMED = [p["id"] for p in U.values() if p["organisation"] == H and p["id"] not in REG_PIDS
           and isinstance(p.get("priceEvidence"), dict) and p["priceEvidence"].get("base")]
PAGE_VAT_YES = next(i for i in UNNAMED if str(U[i]["priceEvidence"].get("includesVat")) == "Yes")
UNNAMED_OTHER = next(i for i in UNNAMED if i != PAGE_VAT_YES)
OTHERS = [p["id"] for p in U.values() if p["organisation"] not in (H,)
          and (p.get("priceEvidence") or {}).get("adjudication") == "adjudicated"
          and not (p.get("priceEvidence") or {}).get("presentationHold")][:2]
FIXTURE = REG_PIDS + [PAGE_VAT_YES, UNNAMED_OTHER] + OTHERS


def snapshot():
    """The Airtable read the generator would see for these products."""
    orgs, products, pricing = {}, [], []
    for pid in FIXTURE:
        p = U[pid]
        oid = orgs.setdefault(p["organisation"], "recORGVAT%08d" % len(orgs))
        products.append(rec(pid, {
            "Product Name": p["name"], "Product Category": "Garden Rooms",
            "Product Code": pid, "Status": "Active", "Verification Status": "Verified",
            "Product URL": p.get("productUrl") or "https://example.ie/" + pid,
            "Organisation": [{"id": oid}]}))
        pe, ref = p["priceEvidence"], p["priceEvidenceRef"]
        f = {"Product": [{"id": pid}], "Base Price": pe.get("base"), "Currency": pe.get("currency"),
             "Price Type": pe.get("priceType"), "Status": pe.get("status"),
             "Last Price Check": ref.get("lastPriceCheck")}
        if pe.get("includesVat"):
            f["Price Includes VAT"] = pe["includesVat"]
        if pe.get("from") is not None:
            f["Price From"] = pe["from"]
        if pe.get("to") is not None:
            f["Price To"] = pe["to"]
        if pe.get("evidenceScope"):
            f["Evidence Scope"] = pe["evidenceScope"]
        pricing.append(rec(ref["recordIds"][0], {k: v for k, v in f.items() if v is not None}))
    return {"products": products, "pricing": pricing, "availability": [], "featureValues": [],
            "features": [],
            "organisations": [rec(oid, {"Organisation Name": name, "Organisation Type": "Manufacturer",
                                        "Website": "https://example.ie/"})
                              for name, oid in orgs.items()]}


def run(tmp, snap, register_doc=None, register_path=None):
    tmp = Path(tmp)
    tmp.mkdir(parents=True, exist_ok=True)
    sp = tmp / "snapshot.json"
    sp.write_text(json.dumps(snap), encoding="utf-8")
    out = tmp / "out"
    args = [sys.executable, str(GEN), "--out-dir", str(out), "--snapshot", str(sp)]
    if register_doc is not None:
        rp = tmp / "vat-terms-evidence.copy.json"
        rp.write_text(json.dumps(register_doc), encoding="utf-8")
        args += ["--vat-terms-register", str(rp)]
    elif register_path is not None:
        args += ["--vat-terms-register", str(register_path)]
    env = dict(os.environ)
    env["PYTHONPATH"] = str(HERE) + (os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else "")
    r = subprocess.run(args, capture_output=True, text=True, env=env)
    uni = out / OUTFILE
    return r, (json.loads(uni.read_text(encoding="utf-8")) if uni.exists() else None)


def refused(label, tmp, snap, reg_doc=None, reg_path=None, needle=None):
    r, uni = run(tmp, snap, reg_doc, reg_path)
    msg = (r.stdout + r.stderr)
    ck(f"{label}: regeneration refused", r.returncode != 0, msg[-300:])
    ck(f"{label}: no universe written", uni is None)
    if needle:
        ck(f"{label}: refusal names the cause", needle in msg, msg[-300:])


print("STAGE 3D-D1 — generator VAT basis (offline, real generator, production register read-only)")
print(f"  register products {len(REG_PIDS)}; fixture products {len(FIXTURE)}")
reg_before = REGISTER.read_bytes()

with tempfile.TemporaryDirectory() as t:
    print("\n  G1  faithful regeneration")
    r, uni = run(t, snapshot(), register_path=REGISTER)
    ck("generator runs", r.returncode == 0, (r.stdout + r.stderr)[-600:])
    if uni:
        got = {p["id"]: p for p in uni["products"]}
        have = {i for i, p in got.items() if (p.get("priceEvidence") or {}).get("vatBasis")}
        ck(f"exactly the {len(REG_PIDS)} register products carry the basis", have == set(REG_PIDS),
           (len(have), sorted(set(REG_PIDS) - have)[:3], sorted(have - set(REG_PIDS))[:3]))
        ck("every basis is 'supplier-terms'",
           all(got[i]["priceEvidence"]["vatBasis"] == "supplier-terms" for i in have))
        keys = ("base", "currency", "priceType", "status", "includesVat", "adjudication", "vatBasis")
        diff = [i for i in REG_PIDS if i in got and any(got[i]["priceEvidence"].get(k) != U[i]["priceEvidence"].get(k) for k in keys)]
        ck("the regenerated price evidence equals the published evidence for all register products", not diff, diff[:3])
        ck("a Hansa24 product with page-stated VAT gets NO inferred basis",
           PAGE_VAT_YES in got and "vatBasis" not in got[PAGE_VAT_YES]["priceEvidence"]
           and got[PAGE_VAT_YES]["priceEvidence"].get("includesVat") == "Yes")
        ck("an unnamed Hansa24 product gets no basis", "vatBasis" not in got[UNNAMED_OTHER]["priceEvidence"])
        ck("other suppliers' products get no basis", all("vatBasis" not in got[i]["priceEvidence"] for i in OTHERS))
        ck("the generator reports the register match", "matching the register exactly" in r.stdout)

    print("\n  N1  expired evidence")
    reg = copy.deepcopy(REG)
    for e in reg["suppliers"]:
        if e["status"] == "accepted":
            e["checked"] = "2026-01-01"; e["expires"] = (dt.date.today() - dt.timedelta(days=1)).isoformat()
    refused("N1 expired", Path(t) / "n1", snapshot(), reg, needle="expired")

    print("\n  N2  incorrect supplier")
    s = snapshot()
    for o in s["organisations"]:
        if o["fields"]["Organisation Name"] == H:
            o["fields"]["Organisation Name"] = "Hansa24 Trading"
    refused("N2 incorrect supplier", Path(t) / "n2", s, reg_path=REGISTER, needle="organisation")

    print("\n  N3  incorrect product")
    reg = copy.deepcopy(REG)
    acc = next(e for e in reg["suppliers"] if e["status"] == "accepted")
    acc["productPagesChecked"][0]["productId"] = OTHERS[0]
    refused("N3 incorrect product", Path(t) / "n3", snapshot(), reg, needle="disagrees")

    print("\n  N4  incorrect price record")
    s = snapshot()
    victim = REG_PIDS[0]
    for prow in s["pricing"]:
        if prow["fields"]["Product"][0]["id"] == victim:
            prow["id"] = "recWRONGPRICE0001"
    refused("N4 incorrect price record", Path(t) / "n4", s, reg_path=REGISTER, needle="price record")

    print("\n  N5  Atlas VAT disagreement")
    s = snapshot()
    for prow in s["pricing"]:
        if prow["fields"]["Product"][0]["id"] == REG_PIDS[1]:
            prow["fields"]["Price Includes VAT"] = "Unknown"
    refused("N5 Atlas VAT not Yes", Path(t) / "n5", s, reg_path=REGISTER, needle="not Yes")

    print("\n  N6  register product absent from Atlas")
    s = snapshot()
    gone = REG_PIDS[2]
    s["products"] = [p for p in s["products"] if p["id"] != gone]
    s["pricing"] = [p for p in s["pricing"] if p["fields"]["Product"][0]["id"] != gone]
    refused("N6 register product absent", Path(t) / "n6", s, reg_path=REGISTER, needle="self-check")

    print("\n  N7  contradictory or invalid register")
    reg = copy.deepcopy(REG); reg["schema"] = "plotnua.vat-terms-evidence.v0"
    refused("N7a unknown schema", Path(t) / "n7a", snapshot(), reg, needle="schema")
    reg = copy.deepcopy(REG)
    acc = next(e for e in reg["suppliers"] if e["status"] == "accepted")
    acc["productPagesChecked"].append(copy.deepcopy(acc["productPagesChecked"][0]))
    refused("N7b product listed twice", Path(t) / "n7b", snapshot(), reg, needle="twice")
    reg = copy.deepcopy(REG)
    acc = next(e for e in reg["suppliers"] if e["status"] == "accepted")
    acc["contraryWordingFound"] = True
    refused("N7c contrary wording recorded", Path(t) / "n7c", snapshot(), reg, needle="safeguards")

    print("\n  N8  register missing")
    refused("N8 register missing", Path(t) / "n8", snapshot(), reg_path=Path(t) / "no-such-register.json",
            needle="could not be read")

ck("the production register was not modified", REGISTER.read_bytes() == reg_before)
print("\n" + "=" * 78)
print(f"  {PASS} passed, {FAIL} failed")
print("=" * 78)
sys.exit(1 if FAIL else 0)
