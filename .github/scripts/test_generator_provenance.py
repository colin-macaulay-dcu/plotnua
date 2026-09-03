#!/usr/bin/env python3
"""
ISSUE 005 PIECE E2.1 — THE REGRESSION TEST THAT WOULD HAVE CAUGHT THE CRASH.

WHY THIS TEST EXISTS.

The 06:15 workflow failed in production with:

    File ".github/scripts/generate_garden_room_universe.py", line 915
      src = txt(cell(product, "    Sources"))
    NameError: name 'product' is not defined. Did you mean: 'by_product'?

`product` is a parameter of `qualify()`, not a name in `main()`; the loop
variable there is `p`. Nothing caught it because no test had ever EXECUTED the
provenance path — the E2 suites read the generator's source text and asserted
on strings, which a NameError sails straight through. Python only binds names
at run time, so a source-text test cannot see this class of bug at all.

So this test RUNS THE REAL GENERATOR, end to end, against a synthetic Airtable
snapshot through the generator's own `--snapshot` switch. No token, no network,
no Airtable. If the provenance line ever loses its scope again, this exits 1.

WHAT THE FIXTURE COVERS, AND WHY EACH CASE IS THERE.

    P1  qualifying   + "    Sources" + a detail Feature   -> provenance emitted
    P2  qualifying   + NO Sources    + a detail Feature   -> NO provenance key
    P3  qualifying   + "    Sources" + NO detail Feature  -> provenance ALONE
    P4  BLOCKED (no Organisation)    + "    Sources"      -> absent entirely

P3 is the case that would have been silently lost: a product whose only
long-form evidence is its source list. P4 records the real, deliberate boundary
— the detail artefact is built inside the `else` of `if q["hardBlockers"]`, so a
blocked product contributes nothing, provenance included.

Run:  python3 test_generator_provenance.py
"""
import json, re, subprocess, sys, tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
GEN = HERE / "generate_garden_room_universe.py"

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


SRC_P1 = "shomera.ie — range pages read 8 Aug 2026; indexed evidence only."
SRC_P3 = "example.ie — supplier catalogue read 1 Sep 2026."

ORG = "recORG00000000001"
# ISSUE 005 PIECE E2.2 — the organisation that broke the first real run.
# Ecohouse Building Systems' IRISH PRESENCE segment is GENUINE Irish-presence
# evidence that happens to cite a landline. The label was right, the selection
# was right, and the VALUE carried personal data. This reproduces that exact
# shape, with the exact number from the failed workflow.
ORG_PHONE_IN_PRESENCE = "recORG00000000002"
FEAT_CONSIDER = "recFEAT0000000001"


def snapshot():
    """An Airtable read in the exact shape fetch_all() returns."""
    def product(pid, name, sources=None, org=True):
        f = {"Product Name": name, "Product Category": "Garden Rooms",
             "Product Code": name.upper().replace(" ", "-"),
             "Status": "Active", "Verification Status": "Partially Verified",
             "Product URL": "https://example.ie/" + name.lower().replace(" ", "-")}
        if sources:
            f["    Sources"] = sources          # leading spaces are Airtable's
        if org:
            f["Organisation"] = [{"id": ORG}]
        return rec(pid, f)

    def fv(fid, pid, text):
        return rec(fid, {"Product": [{"id": pid}], "Feature": [{"id": FEAT_CONSIDER}],
                         "Value Text": text, "Status": "Active",
                         "Confirmation State": "Confirmed",
                         "Evidence Scope": "Product-Specific"})

    return {
        "products": [
            product("recPROD0000000001", "Alpha Room", sources=SRC_P1),
            product("recPROD0000000002", "Beta Room"),
            product("recPROD0000000003", "Gamma Room", sources=SRC_P3),
            product("recPROD0000000004", "Delta Room", sources="never exported", org=False),
            rec("recPROD0000000005", {"Product Name": "Epsilon Room",
                                      "Product Category": "Garden Rooms",
                                      "Product Code": "EPSILON-ROOM", "Status": "Active",
                                      "Verification Status": "Partially Verified",
                                      "Product URL": "https://eco.example.ie/epsilon",
                                      "Organisation": [{"id": ORG_PHONE_IN_PRESENCE}]}),
        ],
        "pricing": [],
        "availability": [],
        "featureValues": [
            fv("recFV000000000001", "recPROD0000000001", "ALPHA. HOMEOWNER IMPLICATION: check the height."),
            fv("recFV000000000002", "recPROD0000000002", "BETA. HOMEOWNER IMPLICATION: check the footprint."),
        ],
        "features": [rec(FEAT_CONSIDER, {"Feature Name": "Considerations"})],
        "organisations": [rec(ORG, {"Organisation Name": "Example Buildings",
                                    "Organisation Type": "Manufacturer",
                                    "Website": "https://example.ie/",
                                    "Headquarters": "HEADQUARTERS: Main St, Cork | "
                                                    "IRISH PRESENCE: Cork premises published | "
                                                    "CONTACT: +353 1 234 5678, sales@example.ie"}),
                          rec(ORG_PHONE_IN_PRESENCE, {
                              "Organisation Name": "Ecohouse-shaped Systems",
                              "Organisation Type": "Manufacturer",
                              "Website": "https://eco.example.ie/",
                              # Verbatim shape of the record that failed the real run.
                              "Headquarters":
                                  "HEADQUARTERS: Unit 9A, Dublin 24 | "
                                  "JURISDICTION: Republic of Ireland | "
                                  "INSTALLATION COVERAGE: INCLUDED IN PRICE | "
                                  "IRISH PRESENCE: Full — Irish premises with Eircode, "
                                  "Irish landline +353 1 253 3786, euro pricing inclusive "
                                  "of VAT, and published business hours Mon-Fri 08:00-17:00 | "
                                  "EVIDENCE TIER: Tier A"})],
    }


def run_generator(gen_path, out_dir, snap_path):
    return subprocess.run(
        [sys.executable, str(gen_path), "--out-dir", str(out_dir), "--snapshot", str(snap_path)],
        capture_output=True, text=True)


def detail_for(out_dir, category):
    f = Path(out_dir) / f"garden-room-detail-{category}-v1.json"
    if not f.exists():
        return None
    return json.loads(f.read_text(encoding="utf-8")).get("products", {})


print("=" * 78)
print("ISSUE 005 E2.1 — THE GENERATOR ACTUALLY RUNS, AND PROVENANCE SURVIVES")
print("=" * 78)

with tempfile.TemporaryDirectory() as td:
    td = Path(td)
    snap = td / "snapshot.json"
    snap.write_text(json.dumps(snapshot()), encoding="utf-8")
    out = td / "out"
    out.mkdir()

    r = run_generator(GEN, out, snap)
    if r.returncode != 0:
        print(r.stdout[-2000:])
        print(r.stderr[-2000:])
    ck("the generator RUNS to completion (exit 0)", r.returncode == 0, r.returncode)
    ck("no NameError anywhere in the run",
       "NameError" not in (r.stdout + r.stderr),
       [l for l in (r.stdout + r.stderr).split("\n") if "NameError" in l][:2])

    combined = json.loads((out / "garden-room-detail-evidence-v1.json").read_text("utf-8"))
    prods = combined.get("products", {})
    srcs = detail_for(out, "sources")

    print("\n--- provenance ---")
    ck("P1 (qualifying, has Sources) carries provenance",
       prods.get("recPROD0000000001", {}).get("sources", {}).get("text") == SRC_P1,
       prods.get("recPROD0000000001", {}).get("sources"))
    ck("P2 (qualifying, NO Sources) has no provenance key",
       "sources" not in prods.get("recPROD0000000002", {}),
       prods.get("recPROD0000000002"))
    ck("P3 (Sources but NO detail Feature) is still carried — provenance alone",
       prods.get("recPROD0000000003", {}).get("sources", {}).get("text") == SRC_P3,
       prods.get("recPROD0000000003"))
    ck("P4 (hard-blocked) contributes nothing at all",
       "recPROD0000000004" not in prods, prods.get("recPROD0000000004"))
    ck("provenance text is VERBATIM — never parsed, split or re-attributed",
       prods.get("recPROD0000000001", {}).get("sources", {}).get("text") == SRC_P1)
    ck("provenance carries no per-field attribution",
       prods.get("recPROD0000000001", {}).get("sources", {}).get("evidenceScope") is None)

    print("\n--- the sources partition is audit-only ---")
    ck("a sources partition IS written for audit", srcs is not None)
    ck("it holds exactly the products that carry Sources",
       sorted(srcs or {}) == ["recPROD0000000001", "recPROD0000000003"], sorted(srcs or {}))
    idx = json.loads((out / "garden-room-detail-index-v1.json").read_text("utf-8"))
    cats = [p["category"] for p in idx["partitions"]]
    ck("the index names the sources partition", "sources" in cats, cats)

    print("\n--- the detail categories still work (nothing regressed) ---")
    con = detail_for(out, "considerations")
    ck("considerations partition carries P1 and P2",
       sorted(con or {}) == ["recPROD0000000001", "recPROD0000000002"], sorted(con or {}))

    print("\n--- supplier evidence (E2a) also executes, and withholds CONTACT ---")
    sup = detail_for(out, "suppliers")
    ck("supplier partition is produced", bool(sup), sup)
    if sup:
        loc = sup.get(ORG, {}).get("locality", {})
        ck("IRISH PRESENCE is exported", loc.get("irishPresence") == "Cork premises published", loc)
        blob = json.dumps(sup)
        ck("no phone number reaches the artefact", "+353" not in blob)
        ck("no email address reaches the artefact", "@example.ie" not in blob)
        ck("no eligibility key is emitted",
           not any(k in blob for k in ("deliveryConfirmed", "excludesIreland",
                                       "excludedProductIds", '"irish"')))

    # ── ISSUE 005 PIECE E2.2 — A CORRECT LABEL CARRYING PERSONAL DATA ─────
    # The first real supplier artefact was refused because Ecohouse's IRISH
    # PRESENCE value cited a landline. The label and the selection were both
    # correct; only the VALUE was unsafe. The whole segment must be withheld —
    # never stripped and salvaged, which would mean deciding where the evidence
    # stops and the personal data starts.
    print("\n--- E2.2: a correct label whose VALUE carries a phone number ---")
    if sup:
        eco = sup.get(ORG_PHONE_IN_PRESENCE, {}).get("locality", {})
        ck("E2.2: irishPresence is WITHHELD, not stripped",
           "irishPresence" not in eco, eco.get("irishPresence"))
        ck("E2.2: no remainder of the unsafe value survives",
           not any("Irish premises" in str(v) for v in eco.values()), eco)
        ck("E2.2: the exact production number is absent from the artefact",
           "+353 1 253 3786" not in json.dumps(sup))
        ck("E2.2: the SAFE labels on the same record still export",
           eco.get("jurisdiction") == "Republic of Ireland"
           and eco.get("installationModel") == "INCLUDED IN PRICE", eco)
        ck("E2.2: no phone survives anywhere in the supplier artefact",
           not re.search(r"\+\d[\d ()-]{7,}", json.dumps(sup)))
        ck("E2.2: no email survives anywhere in the supplier artefact",
           not re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", json.dumps(sup)))

    # ── THE VALIDATOR MUST ACCEPT WHAT THE GENERATOR PRODUCES ─────────────
    # A second E2 defect, found by running this chain: `sources` was written
    # into every product entry but NOT declared in the combined file's
    # `categories`, so the validator refused it —
    #   "category present in the data but not declared: 'sources'"
    # Publication is all-or-none, so that alone would have blocked the whole
    # 06:15 run even after the NameError was fixed. Generating without
    # validating is how that hid; this closes the loop.
    print("\n--- the generator's own output passes the production validator ---")
    v = subprocess.run(
        [sys.executable, str(HERE / "validate_garden_room_detail_evidence.py"),
         "--candidate", str(out / "garden-room-detail-evidence-v1.json"),
         "--index", str(out / "garden-room-detail-index-v1.json"),
         "--output-prefix", str(out) + "/"],
        capture_output=True, text=True)
    ck("the validator ACCEPTS the generated artefact and every partition",
       v.returncode == 0, (v.stdout + v.stderr)[-400:])
    ck("'sources' is declared in the combined file's categories",
       "sources" in combined.get("categories", []), combined.get("categories"))
    ck("'sources' is counted in recordCounts",
       "sources" in (combined.get("recordCounts") or {}), combined.get("recordCounts"))

    # ── E2.2 REINTRODUCED: remove the value-level refusal ──────────────────
    # A guard that cannot fail proves nothing. This strips the E2.2 refusal
    # from a copy of the generator and confirms the production failure returns
    # — the phone reaches the artefact AND the validator refuses it.
    print("\n--- E2.2 guard capability: remove the refusal, the failure returns ---")
    unsafe = td / "unsafe_generator.py"
    gtext = GEN.read_text(encoding="utf-8")
    refusal = ("        if SUPPLIER_PERSONAL_RE.search(value):\n"
               "            return None\n")
    if gtext.count(refusal) != 1:
        ck("E2.2: the refusal is uniquely locatable for the negative test",
           False, gtext.count(refusal))
    else:
        unsafe.write_text(gtext.replace(refusal, ""), encoding="utf-8")
        out3 = td / "out3"
        out3.mkdir()
        r3 = run_generator(unsafe, out3, snap)
        ck("E2.2 REINTRODUCED: the generator still runs (it is a data defect)",
           r3.returncode == 0, r3.returncode)
        sup3 = detail_for(out3, "suppliers") or {}
        ck("E2.2 REINTRODUCED: the phone DOES reach the artefact",
           "+353 1 253 3786" in json.dumps(sup3))
        v3 = subprocess.run(
            [sys.executable, str(HERE / "validate_garden_room_detail_evidence.py"),
             "--candidate", str(out3 / "garden-room-detail-evidence-v1.json"),
             "--index", str(out3 / "garden-room-detail-index-v1.json"),
             "--output-prefix", str(out3) + "/"],
            capture_output=True, text=True)
        ck("E2.2 REINTRODUCED: the validator REFUSES it, exactly as production did",
           v3.returncode != 0 and "personal contact data" in (v3.stdout + v3.stderr),
           (v3.stdout + v3.stderr)[-220:])

    # ── THE BUG, REINTRODUCED ON PURPOSE ───────────────────────────────────
    print("\n--- the guard must be able to fail: reintroduce the exact bug ---")
    broken = td / "broken_generator.py"
    text = GEN.read_text(encoding="utf-8")
    hit = '            src = txt(cell(p, "    Sources"))'
    if text.count(hit) != 1:
        ck("the provenance line is uniquely locatable for the negative test",
           False, text.count(hit))
    else:
        broken.write_text(text.replace(hit, hit.replace("cell(p,", "cell(product,")),
                          encoding="utf-8")
        out2 = td / "out2"
        out2.mkdir()
        r2 = run_generator(broken, out2, snap)
        ck("REINTRODUCED: the generator fails", r2.returncode != 0, r2.returncode)
        ck("REINTRODUCED: it fails with exactly the production NameError",
           "NameError" in (r2.stdout + r2.stderr) and
           "'product' is not defined" in (r2.stdout + r2.stderr),
           (r2.stdout + r2.stderr)[-300:])
        ck("REINTRODUCED: nothing was written",
           not (out2 / "garden-room-detail-evidence-v1.json").exists())

print("\n" + "=" * 78)
print(f"  {PASS} passed, {FAIL} failed")
print("=" * 78)
sys.exit(1 if FAIL else 0)
