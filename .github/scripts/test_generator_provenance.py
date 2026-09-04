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

    def e3(pid, name):
        """A product Atlas has adjudicated out of garden-room recommendations."""
        return rec(pid, {"Product Name": name, "Product Category": "Garden Rooms",
                         "Product Code": pid, "Status": "Active",
                         "Verification Status": "Partially Verified",
                         "Product URL": "https://example.ie/" + pid,
                         "Organisation": [{"id": ORG}]})

    def e3n(pid, name):
        """A LEGITIMATE product whose evidence merely contains the vocabulary."""
        return e3(pid, name)

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
            # ---- ISSUE 005 PIECE E3a — BLOCKER E FIXTURES ------------------
            # THREE that Atlas has adjudicated (must be excluded) and FIVE that
            # merely CONTAIN the tempting vocabulary (must stay eligible). The
            # negative five carry VERBATIM text from the real base — this is the
            # whole reason the contract is two phrases and not a keyword list.
            e3(  "recE3A00000000001", "Hawaii-shaped Garage"),
            e3(  "recE3A00000000002", "Falkland-shaped Garage"),
            e3(  "recE3A00000000003", "Nordic-Ice-shaped Plunge Tub"),
            e3(  "recE3A00000000004", "Wrapped-Phrase Garage"),
            e3n( "recE3A00000000005", "Modern Golf Simulator Room"),
            e3n( "recE3A00000000006", "Large Garden Room Snooker XL 1"),
            e3n( "recE3A00000000007", "ECO Garden Room 6.0m x 3.0m"),
            e3n( "recE3A00000000008", "TimberIN Nordic Rojal"),
            e3n( "recE3A00000000009", "Auroom Quu"),
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
            # ---- E3a POSITIVE: the two authoritative phrases, verbatim -------
            fv("recFVE30000000001", "recE3A00000000001",
               "VERIFIED INTERNAL FLOOR AREA - measurement verified, but DO NOT RANK as a "
               "Garden Room. CATEGORY INTEGRITY - DECISIVE: this is not a garden room. It is "
               "held in Atlas under Garden Rooms and must be excluded from garden-room "
               "recommendations."),
            fv("recFVE30000000002", "recE3A00000000002",
               "CATEGORY INTEGRITY - DECISIVE: this is not a garden room. Lasita states plainly "
               "that it is a garage suitable for two vehicles. It is held in Atlas under Garden "
               "Rooms and must be excluded from garden-room recommendations."),
            # The SECOND phrase, and the CATEGORY ISSUE spelling that broke the
            # conjunctive design in E3a.0.
            fv("recFVE30000000003", "recE3A00000000003",
               "NOT A FLOOR-AREA PRODUCT. DO NOT RANK on internal area - the measure does not "
               "apply. CATEGORY ISSUE: recorded under Garden Rooms but is wellness equipment - "
               "part of the standing misclassification; it must never surface in a garden-room "
               "comparison. Recorded, not corrected."),
            # Whitespace normalisation: the phrase split across a line break and
            # padded with double spaces must still match.
            fv("recFVE30000000004", "recE3A00000000004",
               "CATEGORY INTEGRITY - DECISIVE: this is a garage. It   must be excluded\n"
               "   from garden-room   recommendations."),
            # ---- E3a NEGATIVE: verbatim real prose that must NOT exclude -----
            fv("recFVE30000000005", "recE3A00000000005",
               "A GOLFER WITH A GARDEN AND A SPECIFIC, MEASURABLE REQUIREMENT. This is not a "
               "garden room that happens to fit a simulator - it is designed around one, and "
               "that focus is the reason to choose it."),
            fv("recFVE30000000006", "recE3A00000000006",
               "EXCEEDS THE EXEMPTION ON FOOTPRINT. It sits within the 32-45 m2 range of the "
               "separate Class 3A detached auxiliary dwelling provision, though that route is "
               "for an auxiliary dwelling, not a garden room, and carries its own conditions."),
            fv("recFVE30000000007", "recE3A00000000007",
               "VERIFIED NOMINAL SIZE. DO NOT RANK on internal area. PLANNING: 18 m2, inside the "
               "30 m2 combined allowance; a long narrow proportion changes usable layout without "
               "changing the area figure - a reason area alone should never be the sole ranking "
               "input."),
            fv("recFVE30000000008", "recE3A00000000008",
               "NOT A FLOOR-AREA PRODUCT. A wood-fired hot tub is a vessel, not an enclosed "
               "structure. DO NOT RANK on internal area - the measure does not apply. CATEGORY "
               "INTEGRITY: wellness equipment recorded under Garden Rooms; standing TimberIN "
               "misclassification."),
            fv("recFVE30000000009", "recE3A00000000009",
               "NO AREA PUBLISHED. DO NOT RANK on any basis. CATEGORY INTEGRITY: Auroom supplies "
               "wellness/sauna cabins, previously recorded as a category misclassification; Atlas "
               "has no correct Product Category option for them, and they should not be compared "
               "like-for-like against work-use garden rooms."),
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
    # E3a widened the fixture, so assert the INVARIANT rather than a frozen list:
    # the original two are present, and no adjudicated product ever is.
    ck("considerations partition carries P1 and P2",
       {"recPROD0000000001", "recPROD0000000002"} <= set(con or {}), sorted(con or {}))
    ck("considerations partition carries no adjudicated product",
       not (set(con or {}) & {"recE3A00000000001", "recE3A00000000002",
                              "recE3A00000000003", "recE3A00000000004"}),
       sorted(set(con or {}) & {"recE3A00000000001", "recE3A00000000002",
                                "recE3A00000000003", "recE3A00000000004"}))

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

    # ── ISSUE 005 PIECE E3a — BLOCKER E ────────────────────────────────────
    print("\n--- E3a: category-integrity adjudication (Blocker E) ---")
    uni = json.loads((out / "garden-room-recommendation-universe-v1.json").read_text("utf-8"))
    exc = json.loads((out / "garden-room-exclusions-v1.json").read_text("utf-8"))
    elig_ids = {p["productId"] for p in uni["products"]}
    exc_by_id = {e["productId"]: e for e in exc["excluded"]}

    def blocker_codes(pid):
        e = exc_by_id.get(pid)
        return {b["code"] for b in e["qualification"]["hardBlockers"]} if e else set()

    POSITIVE = {
        "recE3A00000000001": "must be excluded from garden-room recommendations",
        "recE3A00000000002": "must be excluded from garden-room recommendations",
        "recE3A00000000003": "must never surface in a garden-room comparison",
        "recE3A00000000004": "must be excluded from garden-room recommendations",
    }
    NEGATIVE = ["recE3A00000000005", "recE3A00000000006", "recE3A00000000007",
                "recE3A00000000008", "recE3A00000000009"]

    for pid, phrase in POSITIVE.items():
        ck(f"E3a EXCLUDED: {pid} is not in the recommendation universe",
           pid not in elig_ids)
        ck(f"E3a EXCLUDED: {pid} carries Blocker E", "E" in blocker_codes(pid),
           blocker_codes(pid))
        b = [x for x in (exc_by_id.get(pid) or {}).get("qualification", {})
             .get("hardBlockers", []) if x["code"] == "E"]
        ck(f"E3a EXCLUDED: {pid} names the phrase that authorised it",
           bool(b) and b[0].get("evidence") == phrase, b[0].get("evidence") if b else None)
        ck(f"E3a EXCLUDED: {pid} names the authorising Feature Value record",
           bool(b) and str(b[0].get("evidenceRecordId", "")).startswith("recFVE3"),
           b[0].get("evidenceRecordId") if b else None)

    ck("E3a: the whitespace-wrapped phrase still matched",
       "recE3A00000000004" not in elig_ids)

    for pid in NEGATIVE:
        ck(f"E3a ELIGIBLE: {pid} survives — prose is not an adjudication",
           pid in elig_ids, sorted(blocker_codes(pid)))
        ck(f"E3a ELIGIBLE: {pid} carries no Blocker E", "E" not in blocker_codes(pid))

    ck("E3a: exactly four products excluded by Blocker E",
       sum(1 for e in exc["excluded"]
           if any(b["code"] == "E" for b in e["qualification"]["hardBlockers"])) == 4)
    ck("E3a: blockers A-D still fire independently (the pre-existing blocked product)",
       "recPROD0000000004" in exc_by_id and "E" not in blocker_codes("recPROD0000000004"),
       sorted(blocker_codes("recPROD0000000004")))
    ck("E3a: totals reconcile", len(uni["products"]) + exc["excludedCount"]
       == uni["sourceGardenRoomCount"],
       (len(uni["products"]), exc["excludedCount"], uni["sourceGardenRoomCount"]))

    # §8 — the ESTABLISHED contract: detail evidence is built inside the `else`
    # of `if hardBlockers`, so an excluded product contributes none. Its research
    # is preserved in Airtable and in the exclusions audit, which carries the
    # full qualification record. Following the contract, not inventing one.
    ck("E3a: excluded products contribute no detail evidence (D4b contract)",
       all(pid not in prods for pid in POSITIVE), [p for p in POSITIVE if p in prods])
    ck("E3a: their evidence IS preserved in the exclusions audit",
       all(pid in exc_by_id for pid in POSITIVE))

    # ── E3a NEGATIVE REGRESSION: remove the blocker, eligibility returns ────
    print("\n--- E3a guard capability: neutralise Blocker E ---")
    noe = td / "no_blocker_e.py"
    gt = GEN.read_text(encoding="utf-8")
    call = ("    adjudication = category_exclusion(\n"
            "        all_feat_rows if all_feat_rows is not None else feat_rows)\n")
    if gt.count(call) != 1:
        ck("E3a: the blocker call is uniquely locatable", False, gt.count(call))
    else:
        noe.write_text(gt.replace(call, "    adjudication = None\n"), encoding="utf-8")
        out4 = td / "out4"
        out4.mkdir()
        r4 = run_generator(noe, out4, snap)
        ck("E3a REMOVED: the generator still runs", r4.returncode == 0, r4.returncode)
        uni4 = json.loads((out4 / "garden-room-recommendation-universe-v1.json").read_text("utf-8"))
        elig4 = {p["productId"] for p in uni4["products"]}
        ck("E3a REMOVED: all four adjudicated products become eligible again",
           all(pid in elig4 for pid in POSITIVE),
           [p for p in POSITIVE if p not in elig4])
        ck("E3a REMOVED: eligible count rises by exactly four",
           len(elig4) == len(elig_ids) + 4, (len(elig_ids), len(elig4)))

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
