#!/usr/bin/env python3
"""STAGE 3D-D1 — Rayco wording and the generator VAT-basis safeguard: the release proof.

    python3 atlas-tools/prove-stage3d-d1.py

  D1  scope: against BASE, only the approved files differ; the universe, Search
      index, hold register, VAT register, guide evidence and every public page
      except your-plot.html are byte-identical (no matching rule, no counts, no data)
  D2  Rayco's wording across all products (prove-rayco-site-works-wording.mjs),
      plus four planted faults that must each be refused
  D3  Rayco's hold is unchanged: the hold register and the six protected
      products' records equal BASE; Rayco has no Search price
  D4  the generator rebuilds vatBasis offline (test_generator_vat_basis.py)
  D5  the validator accepts production and refuses each planted VAT fault
"""
import copy, hashlib, json, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = "b7cb4dd"
# STAGE 3D-D2: the scope, data-identity and hold-identity checks below are pinned to the
# Stage 3D-D1 release commit itself, so later approved stages (3D-D2 moves the universe,
# Search and pages on purpose) do not re-open this proof. The live tree's holds, Rayco
# wording and VAT basis are re-proven by prove-matching-eligibility.py.
RELEASE = "34705c4"
ALLOWED = {
    "your-plot.html",
    ".github/scripts/generate_garden_room_universe.py",
    ".github/scripts/validate_garden_room_universe.py",
    ".github/scripts/test_generator_provenance.py",
    ".github/scripts/test_generator_vat_basis.py",
    "atlas-tools/prove-rayco-site-works-wording.mjs",
    "atlas-tools/prove-stage3d-d1.py",
}
UNI = "garden-room-recommendation-universe-v1.json"
PROTECTED = {"recDa5vihxcYG9xoH": "NOOK 1", "rectQX4XpBbD6H3LU": "NOOK 2", "rec45XRwQ4qqGCQbv": "ECC 1",
             "recCF6Fdi2i1Qo04Z": "ECC 2", "recDIcUb7S6pP8JCx": "Rayco", "recej5DFaBD76ODlv": "PREMIUM S"}
ok, bad = [], []


def check(n, c, d=""):
    (ok if c else bad).append(n + ("" if c else " — " + str(d)[:300]))


def git(*a):
    return subprocess.run(["git", *a], cwd=ROOT, capture_output=True).stdout


def base_bytes(path):
    return git("show", f"{BASE}:{path}")


# D1 — scope
changed = set(git("diff", "--name-only", BASE, RELEASE).decode().split())
check("D1 only the approved files differ between %s and the release %s" % (BASE, RELEASE), changed <= ALLOWED,
      sorted(changed - ALLOWED))
for f in (UNI, "search-index-v1.json", "atlas-tools/price-presentation-holds.json",
          "atlas-tools/vat-terms-evidence.json", "atlas-tools/garden-room-price-page-evidence.json",
          "garden-room-prices-ireland.html", "discovery-living-in-the-garden.html", "search.js",
          ".github/workflows/atlas-match-universe-refresh.yml"):
    check(f"D1 {f} byte-identical to {BASE} at the release", git("show", f"{RELEASE}:{f}") == base_bytes(f))

# D2 — Rayco wording, all products, plus planted faults
with tempfile.TemporaryDirectory() as t:
    bp = Path(t) / "your-plot.base.html"
    bp.write_bytes(base_bytes("your-plot.html"))
    cp = Path(t) / "your-plot.release.html"
    cp.write_bytes(git("show", f"{RELEASE}:your-plot.html"))
    up = Path(t) / "universe.release.json"
    up.write_bytes(git("show", f"{RELEASE}:{UNI}"))
    args = ["node", str(ROOT / "atlas-tools/prove-rayco-site-works-wording.mjs"), str(cp), str(bp), str(up)]
    r = subprocess.run(args, capture_output=True, text=True)
    check("D2 Rayco wording proof passes (all products; exactly one changed)", r.returncode == 0,
          (r.stdout + r.stderr)[-500:])
    for fault, label in (("price-visible", "7 Rayco historical price becoming visible"),
                         ("foundations-included", "8 Rayco foundations described as included"),
                         ("unrelated-wording", "9 an unrelated product's wording changing"),
                         ("turnkey-label", "Rayco label reverting to turnkey")):
        r = subprocess.run(args + ["--plant", fault], capture_output=True, text=True)
        check(f"D2 planted fault {label}: refused", r.returncode == 1, r.stdout[-200:])

# D3 — holds unchanged
U = {p["id"]: p for p in json.loads(git("show", f"{RELEASE}:{UNI}"))["products"]}
UB = {p["id"]: p for p in json.loads(base_bytes(UNI))["products"]}
for pid, name in PROTECTED.items():
    check(f"D3 {name} record identical to {BASE}", U.get(pid) == UB.get(pid))
ray = U["recDIcUb7S6pP8JCx"]
h = (ray.get("priceEvidence") or {}).get("presentationHold") or {}
check("D3 Rayco: historical price kept, withheld, excluded from matching",
      ray.get("price") == 29500 and h.get("figure") == "withheld" and h.get("matching") == "excluded"
      and ray.get("priceSafeForMatching") is False and ray.get("priceStatus") == "Partially Verified")
si = json.loads(git("show", f"{RELEASE}:search-index-v1.json"))
si = si["records"] if isinstance(si, dict) else si
rs = [x for x in si if x.get("id") == "prod-recDIcUb7S6pP8JCx"]
check("D3 Rayco: in Search, with no price", len(rs) == 1 and "price" not in rs[0], rs)

# D4 — generator
r = subprocess.run([sys.executable, str(ROOT / ".github/scripts/test_generator_vat_basis.py")],
                   capture_output=True, text=True)
check("D4 generator rebuilds vatBasis and refuses every contradiction (offline suite)",
      r.returncode == 0 and " 0 failed" in r.stdout, r.stdout[-600:])

# D5 — validator
VAL = ROOT / ".github/scripts/validate_garden_room_universe.py"
doc = json.loads(git("show", f"{RELEASE}:{UNI}"))
REGP = ROOT / "atlas-tools/vat-terms-evidence.json"
reg = json.loads(REGP.read_text())
acc = next(e for e in reg["suppliers"] if e["status"] == "accepted")
first = acc["productPagesChecked"][0]["productId"]
other = next(p["id"] for p in doc["products"] if p["organisation"] != acc["organisation"]
             and isinstance(p.get("priceEvidence"), dict))


def validate(cand_doc, prod=True, as_of=None, reg_doc=None):
    with tempfile.TemporaryDirectory() as t:
        cp = Path(t) / UNI
        cp.write_text(json.dumps(cand_doc))
        a = [sys.executable, str(VAL), "--candidate", str(cp)]
        if prod:
            pp = Path(t) / "production.json"; pp.write_text(json.dumps(doc)); a += ["--production", str(pp)]
        if as_of:
            a += ["--as-of", as_of]
        if reg_doc is not None:
            rp = Path(t) / "reg.json"; rp.write_text(json.dumps(reg_doc)); a += ["--vat-terms-register", str(rp)]
        return subprocess.run(a, capture_output=True, text=True)


# The Stage 3D-D1 release universe predates R-MATCH's priceState (Stage 3D-D2), so the
# validator's VAT-basis rule is exercised here and its R-MATCH errors are set aside.
def vat_only(r):
    lines = [l for l in r.stdout.splitlines() if l.strip().startswith("- ")]
    return [l for l in lines if "R-MATCH" not in l]


r = validate(doc)
check("D5 validator raises no VAT-basis problem on the release universe", not vat_only(r), r.stdout[-300:])


def mutate(fn):
    d = copy.deepcopy(doc)
    fn({p["id"]: p for p in d["products"]})
    return d


faults = [
    ("1 missing vatBasis", mutate(lambda P: P[first]["priceEvidence"].pop("vatBasis")), {}),
    ("1b missing vatBasis, judged on the register alone (no production)", mutate(lambda P: P[first]["priceEvidence"].pop("vatBasis")), {"prod": False}),
    ("2 expired VAT evidence", doc, {"as_of": "2027-02-06"}),
    ("3 incorrect supplier", mutate(lambda P: P[first].__setitem__("organisation", "Hansa24 Trading")), {}),
    ("4 incorrect product (basis on a product the register does not name)",
     mutate(lambda P: P[other]["priceEvidence"].__setitem__("vatBasis", "supplier-terms")), {}),
    ("5 incorrect price record", mutate(lambda P: P[first]["priceEvidenceRef"].__setitem__("recordIds", ["recWRONGPRICE0001"])), {}),
    ("6 Atlas VAT disagreement", mutate(lambda P: P[first]["priceEvidence"].__setitem__("includesVat", "Unknown")), {}),
    ("unknown vatBasis value", mutate(lambda P: P[first]["priceEvidence"].__setitem__("vatBasis", "assumed")), {}),
]
for label, d, kw in faults:
    r = validate(d, prod=kw.get("prod", True), as_of=kw.get("as_of"))
    check(f"D5 validator refuses: {label}", r.returncode == 1 and any("VAT" in l for l in vat_only(r)), r.stdout[-300:])
r = validate(doc, reg_doc={**reg, "schema": "x"})
check("D5 validator refuses: invalid register schema", r.returncode == 1, r.stdout[-200:])

print("\n".join("PASS  " + x for x in ok))
print("\n".join("FAIL  " + x for x in bad))
print(f"\nSTAGE 3D-D1 · {len(ok)} passed, {len(bad)} failed")
sys.exit(1 if bad else 0)
