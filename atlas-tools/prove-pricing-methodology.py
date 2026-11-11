#!/usr/bin/env python3
"""PlotNua · Stage 3D-C2 pricing methodology proof (founder approval 7 Nov 2026).

Runs the PRODUCTION price-guide builder (render, fill, page guards, R-VAT, R-INSTALLED, the
commercial-disclosure check) on the committed evidence, then plants each fault the Stage 3D-C1
package named and requires the build to refuse it.

  M1  the committed guide builds and its figures are the ones published
  M2  installed and finished: every published supplier's base is shown included (R-INSTALLED)
  M3  foundations excluded and base not stated are founder-held; supply only stays held
  M4  VAT rule B: only register-accepted Hansa24 products carry vatBasis; Irish Log Cabins and
      Powersheds stay not-relied-on; every accepted entry is current
  M5  the retired statistic is gone from the guide and Living in the Garden
  M6  protected holds (NOOK, ECC, Rayco, PREMIUM S) and their published records are unchanged
      against --base (default 59eef1e)
  M7  planted faults, each must be refused

  python3 atlas-tools/prove-pricing-methodology.py [--base REV] [--today YYYY-MM-DD]
"""
import copy, hashlib, importlib.util, json, pathlib, subprocess, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
BASE = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--base=")), "59eef1e")
TODAY = next((a.split("=", 1)[1] for a in sys.argv if a.startswith("--today=")), "2026-11-07")
sys.argv = [sys.argv[0], "--today=" + TODAY]


class Refused(Exception):
    pass


def die(msg):
    raise Refused(msg)


spec = importlib.util.spec_from_file_location("grp", ROOT / "atlas-tools" / "build-garden-room-prices.py")
b = importlib.util.module_from_spec(spec)
spec.loader.exec_module(b)
b.die = die
cd_spec = importlib.util.spec_from_file_location("cd", ROOT / "atlas-tools" / "check-commercial-disclosure.py")
cd = importlib.util.module_from_spec(cd_spec)
cd_spec.loader.exec_module(cd)

EV = json.loads((ROOT / "atlas-tools/cluster1-cost-evidence.json").read_text())
EX = json.loads((ROOT / "atlas-tools/garden-room-price-page-evidence.json").read_text())
PAGE = (ROOT / "garden-room-prices-ireland.html").read_text()
U = {p["productId"]: p for p in json.loads((ROOT / "garden-room-recommendation-universe-v1.json").read_text())["products"]}
REG0 = json.loads(b.VAT_REGISTER.read_text())
EXTRAS0 = json.loads(b.EXTRAS.read_text())
ORG = {r["productId"]: U[r["productId"]]["organisation"] for r in EX["rows"]}
fails, notes = [], []


def ok(cond, msg):
    (notes if cond else fails).append(("PASS " if cond else "FAIL ") + msg)


def build(ev=None, ex=None, page=None, reg=None, extras=None, held=None):
    """The production build on (possibly modified) inputs. Returns the page or raises Refused."""
    tmp = pathlib.Path(tempfile.mkdtemp())
    saved = (b.VAT_REGISTER, b.EXTRAS, dict(b.FOUNDER_HELD))
    try:
        if reg is not None:
            (tmp / "reg.json").write_text(json.dumps(reg)); b.VAT_REGISTER = tmp / "reg.json"
        if extras is not None:
            (tmp / "ex.json").write_text(json.dumps(extras)); b.EXTRAS = tmp / "ex.json"
        if held is not None:
            b.FOUNDER_HELD.clear(); b.FOUNDER_HELD.update(held)
        regions, facts = b.render(ev or EV, ex or EX)
        out = b.fill(page or PAGE, regions)
        b.page_guards(out, (ex or EX)["rows"], regions["_DESC"])
        reg_, _, _, litg = cd.load()
        for p in cd.problems(reg_, ex or EX, out, litg):
            die("COMMERCIAL " + p)
        return out, facts
    finally:
        b.VAT_REGISTER, b.EXTRAS = saved[0], saved[1]
        b.FOUNDER_HELD.clear(); b.FOUNDER_HELD.update(saved[2])


def refused(name, fn):
    try:
        fn()
    except Refused as e:
        notes.append("CAUGHT  %s -- %s" % (name, str(e)[:110]))
        return 1
    fails.append("MISSED  %s" % name)
    return 0


def rows_with(edit):
    ex = copy.deepcopy(EX)
    edit(ex["rows"])
    return ex


def ev_for(ex):
    """Evidence recomputed from modified rows, so a fault reaches the guard under test rather
    than the evidence-agreement check (which would refuse it first)."""
    ev = copy.deepcopy(EV)
    ev["segments"] = b.summarise(ex["rows"])
    return ev


# ---- M1
out, facts = build()
ok(out == PAGE, "M1 the committed page is exactly what the builder produces")
t = facts["published"]["INSTALLED_FINISHED_TURNKEY"]; k = facts["published"]["UNKNOWN_DIY_OR_INSTALLED"]
notes.append("     installed %s-%s (%d/%d), kit %s-%s (%d/%d), fresh until %s, prices in ranges %d"
             % (t["minEur"], t["maxEur"], t["n"], t["organisations"], k["minEur"], k["maxEur"], k["n"],
                k["organisations"], facts["freshUntil"], facts["pricesInPublishedRanges"]))
ok(list(facts["published"]) == ["INSTALLED_FINISHED_TURNKEY", "UNKNOWN_DIY_OR_INSTALLED"],
   "M1 exactly two groups are published: installed and finished, kit or self-build")
# ---- M2
inst = {ORG[r["productId"]] for r in EX["rows"] if r["segment"] == "INSTALLED_FINISHED_TURNKEY" and r["lastPriceCheck"]}
# 11 Nov 2026 (founder decision): Garden Office Solutions is temporarily unable to take new orders;
# its four prices leave the evidence through the registered correction, not by any rule change here.
_reg = json.loads((ROOT / "atlas-tools" / "cost-evidence-corrections.json").read_text(encoding="utf-8"))
_withdrawn = {p["id"] for c in _reg["corrections"] if c["id"] == "availability-and-reverification-2026-11-11"
              for p in c["products"] if p["expect"] == "evidenceExcluded"}
ok({"recKHXaApIugjOKti", "recUs4gexxlfkaiUj", "reciolethPMEn50gQ", "recUnUAWq0TWkNO5C"} <= _withdrawn,
   "M2 Garden Office Solutions' four prices are withdrawn by the registered 11 Nov 2026 correction")
ok(inst == {"Garden Rooms", "Modular House", "Shomera"},
   "M2 the published installed suppliers are the three with the base shown included: %s" % sorted(inst))
ok(all(s["base"]["state"] == "included" for s in EXTRAS0["suppliers"]), "M2 every extras entry shows the base included")
# ---- M3
segs = {}
for r in EX["rows"]:
    segs.setdefault(ORG[r["productId"]], set()).add(r["segment"])
ok(segs["Adman Steel Sheds"] == {"INSTALLED_FINISHED_FOUNDATIONS_EXCLUDED"}, "M3 Adman: installed, foundations excluded")
ok(segs["ÖÖD House"] == {"SUPPLY_ONLY_INSTALL_SEPARATE"}, "M3 ÖÖD: supply only, installation extra")
ok(segs["Live in Garden Pods"] == {"INSTALLED_BASE_NOT_STATED"}, "M3 Live in Garden Pods: installed, base not stated")
ok(segs["Loghouse"] == {"SUPPLIED_AND_ERECTED"}, "M3 Loghouse unchanged: supplied and erected")
ok(segs["Modular House"] == {"INSTALLED_FINISHED_TURNKEY"}, "M3 Modular House: installed and finished")
for o in ("Pineca Ireland", "Hansa24 Group", "Powersheds"):
    ok(segs[o] == {"UNKNOWN_DIY_OR_INSTALLED"}, "M3 %s: kit or self-build" % o)
for kk in ("SUPPLY_ONLY_INSTALL_SEPARATE", "INSTALLED_FINISHED_FOUNDATIONS_EXCLUDED", "INSTALLED_BASE_NOT_STATED"):
    ok(kk in b.FOUNDER_HELD and kk not in facts["published"], "M3 %s founder-held and unpublished" % kk)
ok(not any(r["segment"] == "UNKNOWN_NOTHING_PUBLISHED" for r in EX["rows"]), "M3 no price is left 'not stated'")
# ---- M4
reg = {e["organisation"]: e for e in REG0["suppliers"]}
ok(reg["Hansa24 Group"]["status"] == "accepted" and len(reg["Hansa24 Group"]["productPagesChecked"]) == 21,
   "M4 Hansa24 accepted for 21 checked products")
ok(reg["Irish Log Cabins"]["status"] == "not-relied-on" and reg["Powersheds"]["status"] == "not-relied-on",
   "M4 Irish Log Cabins and Powersheds not relied on")
vb = sorted(p for p, x in U.items() if (x.get("priceEvidence") or {}).get("vatBasis"))
ok(vb == sorted(x["productId"] for x in reg["Hansa24 Group"]["productPagesChecked"]),
   "M4 exactly the 21 register products carry vatBasis in the universe")
ok(all(ORG[r["productId"]] not in ("Irish Log Cabins", "Powersheds") or r["vat"] != "Yes" for r in EX["rows"]),
   "M4 no Irish Log Cabins or Powersheds price counts as VAT-inclusive")
ok(all(not (U[p].get("priceEvidence") or {}).get("vatBasis") or U[p]["organisation"] == "Hansa24 Group" for p in U),
   "M4 vatBasis only on Hansa24")
# ---- M5
litg = (ROOT / "discovery-living-in-the-garden.html").read_text()
ok(not b.RETIRED_STATISTIC.search(PAGE) and not b.RETIRED_STATISTIC.search(litg),
   "M5 the retired statistic is on neither the guide nor Living in the Garden")
ok("Not every garden-room price covers the same" in litg and b.COMPARE_EXPLANATION in PAGE,
   "M5 the approved explanation is on both pages")
# ---- M6
def at(rev, f):
    return subprocess.run(["git", "show", "%s:%s" % (rev, f)], cwd=ROOT, capture_output=True).stdout
# 11 Nov 2026 (founder approval): exactly six holds are added (figure withheld) with their decision
# note; every earlier hold and every other byte of the register's content is unchanged.
SIX_2026_11_11 = {"recKHXaApIugjOKti", "recUs4gexxlfkaiUj", "reciolethPMEn50gQ", "recUnUAWq0TWkNO5C",
                  "recBVDyal8VGGVEZM", "reczxM0lggLXTBCdU"}
_hc = json.loads((ROOT / "atlas-tools/price-presentation-holds.json").read_text(encoding="utf-8"))
_new = [h for h in _hc["holds"] if h["productId"] in SIX_2026_11_11]
_hc["holds"] = [h for h in _hc["holds"] if h["productId"] not in SIX_2026_11_11]
_hc.pop("decision_2026_11_11", None)
ok(json.loads(at(BASE, "atlas-tools/price-presentation-holds.json")) == _hc,
   "M6 price-presentation holds identical to %s apart from the six approved 11 Nov 2026 holds" % BASE)
ok(sorted(h["productId"] for h in _new) == sorted(SIX_2026_11_11) and all(h.get("figure") == "withheld" for h in _new)
   and all(U[pid].get("priceState") == "held" and not U[pid].get("priceFreshUntil") and U[pid].get("priceSafeForMatching") is False
           for pid in SIX_2026_11_11),
   "M6 the six 11 Nov 2026 holds are present, figure withheld, held and out of matching")
base_u = {p["productId"]: p for p in json.loads(at(BASE, "garden-room-recommendation-universe-v1.json"))["products"]}
held = [p for p, x in base_u.items() if (x.get("priceEvidence") or {}).get("presentationHold")]
# Stage 3D-D2 (founder approval 7 Nov 2026) adds the R-MATCH presentation keys
# priceState / priceFreshUntil to every record; a held record must carry
# priceState "held" and no expiry. Every other byte is unchanged.
D2 = ("priceState", "priceFreshUntil")
def d2(x):
    return {f: v for f, v in x.items() if f not in D2}
ok(held and all(d2(base_u[p]) == d2(U[p]) for p in held), "M6 all %d held records byte-identical to %s (NOOK, ECC, Rayco, PREMIUM S), apart from the 3D-D2 price state" % (len(held), BASE))
ok(held and all(U[p].get("priceState") == "held" and not U[p].get("priceFreshUntil") for p in held), "M6 every held record is in the held price state, with no expiry")
ok(all(U[p].get("organisation") not in ("NOOK Prefab (espacio NOOK)", "East Coast Carpentry", "Rayco Modular Homes")
       or d2(base_u[p]) == d2(U[p]) for p in U if p in base_u), "M6 every NOOK, ECC and Rayco record byte-identical")

# ---- M7 planted faults
n = 0
def mv(org, seg):
    return lambda rows: [r.update(segment=seg) for r in rows if ORG[r["productId"]] == org]
for name, org, seg in (("Adman back in installed and finished", "Adman Steel Sheds", "INSTALLED_FINISHED_TURNKEY"),
                       ("Live in Garden Pods in installed and finished", "Live in Garden Pods", "INSTALLED_FINISHED_TURNKEY")):
    ex = rows_with(mv(org, seg)); n += refused(name, lambda ex=ex: build(ev=ev_for(ex), ex=ex))
x = copy.deepcopy(EXTRAS0); x["suppliers"][0]["base"]["state"] = "notEstablished"
n += refused("an installed supplier whose base is not established", lambda: build(extras=x))
h = dict(b.FOUNDER_HELD); h.pop("INSTALLED_FINISHED_FOUNDATIONS_EXCLUDED"); h.pop("INSTALLED_BASE_NOT_STATED")
def fx3(rows):
    for r in rows:
        if ORG[r["productId"]] in ("Adman Steel Sheds", "Live in Garden Pods", "Garden Office Solutions"):
            r["segment"] = "INSTALLED_FINISHED_FOUNDATIONS_EXCLUDED"
ex = rows_with(fx3)
def held_published():
    page, f = build(ev=ev_for(ex), ex=ex, held=h)
    if "INSTALLED_FINISHED_FOUNDATIONS_EXCLUDED" in f["published"]:
        die("foundations-excluded would be published once the hold is lifted")
n += refused("foundations excluded published without its founder hold", held_published)
def sp(rows):
    for r in rows:
        if r["price"] == 149900:
            r["segment"] = "UNKNOWN_DIY_OR_INSTALLED"
ex = rows_with(sp); n += refused("a 149,900 price inside a published range", lambda: build(ev=ev_for(ex), ex=ex))
def ilc(rows):
    for r in rows:
        if ORG[r["productId"]] == "Irish Log Cabins":
            r["vat"] = "Yes"; r["vatBasis"] = "supplier-terms"
ex = rows_with(ilc); n += refused("Irish Log Cabins VAT counted on its 13.5% statement", lambda: build(ev=ev_for(ex), ex=ex))
def pw(rows):
    for r in rows:
        if ORG[r["productId"]] == "Powersheds":
            r["vat"] = "Yes"; r["vatBasis"] = "supplier-terms"
ex = rows_with(pw); n += refused("Powersheds VAT counted with no statement", lambda: build(ev=ev_for(ex), ex=ex))
def expired():
    saved = b.TODAY
    b.TODAY = b.dt.date.fromisoformat(reg["Hansa24 Group"]["expires"]) + b.dt.timedelta(days=1)
    try:
        b.vat_guards(EX["rows"])
    finally:
        b.TODAY = saved
n += refused("a supplier-terms VAT position after the register expires", expired)
r2 = copy.deepcopy(REG0); r2["suppliers"][0]["contraryWordingFound"] = True
n += refused("a product page with contrary VAT wording", lambda: build(reg=r2))
r3 = copy.deepcopy(REG0); r3["suppliers"][0]["rateCheck"]["result"] = "inconsistent"
n += refused("the rate-consistency safeguard failed", lambda: build(reg=r3))
def drop(rows):
    for r in rows:
        if r.get("vatBasis"):
            r.pop("vatBasis"); break
ex = rows_with(drop); n += refused("a register-accepted price that lost its supplier-terms basis", lambda: build(ex=ex))
def promo(rows):
    for r in rows:
        if ORG[r["productId"]] == "Hansa24 Group":
            r["price"] -= 500; break
FROZEN = b.freeze(EV)["rows"]
ok(FROZEN == EX["rows"], "M1 the committed extract is exactly the snapshot plus the registered corrections")
def unregistered(ex):
    build(ex=ex)
    if ex["rows"] != FROZEN:
        die("the extract differs from the snapshot plus the registered corrections (--freeze --check)")
ex = rows_with(promo); n += refused("a promotional or unapproved price", lambda: unregistered(ex))
ex = rows_with(lambda rows: rows.__setitem__(slice(None), [r for r in rows if ORG[r["productId"]] != "Powersheds"]))
n += refused("Powersheds dropped from the ranges to extend freshness", lambda: build(ex=ex))
n += refused("the retired statistic back on the page", lambda: b.page_guards(
    PAGE.replace('<div class="pr-stats">', '<div class="pr-stats">\n  <p class="pr-stat"><span class="pr-stat-n">168</span>'
                 '<span class="pr-stat-l">of 237 published prices do not establish what the price includes</span></p>', 1),
    EX["rows"], b.description(t)))
n += refused("a founder-held group's label inside the price table", lambda: b.page_guards(
    PAGE.replace("<span class=\"pr-basis\">Installed and finished</span>",
                 "<span class=\"pr-basis\">Installed, but foundations excluded</span>", 1), EX["rows"], b.description(t)))
n += refused("the VAT footnote removed", lambda: b.page_guards(PAGE.replace(b.VAT_FOOTNOTE, "", 1), EX["rows"], b.description(t)))
nk = {"priceEvidenceRef": {"basisLeadPhrase": None}, "priceBasisConfidence": "NO_BASIS_STATED", "features": {}}
def kit_without_evidence():
    if b.segment(nk) == "UNKNOWN_DIY_OR_INSTALLED":
        return
    die("a record with no installation evidence is not labelled a kit")
n += refused("a kit label on a record without DIY evidence", kit_without_evidence)
TOTAL = 17
ok(n == TOTAL, "M7 planted faults caught %d/%d" % (n, TOTAL))

for l in notes:
    print("  " + l)
for l in fails:
    print("  " + l)
if fails:
    print("PRICING METHODOLOGY · REFUSED — %d problem(s)" % len(fails)); sys.exit(2)
print("PRICING METHODOLOGY · OK — M1-M6 pass; faults %d/%d caught" % (n, TOTAL))
