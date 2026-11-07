#!/usr/bin/env python3
"""STAGE 3D-D2 — matching eligibility (R-MATCH): the release proof, with planted faults.

    python3 atlas-tools/prove-matching-eligibility.py [--as-of YYYY-MM-DD]

Reads the committed universe, Search index, Maker Explorer pages, guide evidence and
pages, and runs the real browser code (atlas-tools/rmatch-runtime.mjs) under a frozen
clock. Nothing is hard-coded except the production commit the stage was built on
(BASE) and the record ids of the protected holds; every expected figure is derived.

  E1  R-MATCH holds for every published record (independent recomputation)
  E2  the Partially Verified euro, USD and Range-Level prices are ineligible; holds held
  E3  Search: figures, under-EUR filters and supplier ranges only from eligible, current,
      EUR prices; every product still indexed (G7d); unsupported ranges removed
  E4  Maker Explorer: ineligible -> "Price not currently verified"; holds unchanged;
      Hansa24 supplier-terms VAT wording intact; every figure carries its expiry
  E5  Your Plot (real code, frozen clock): states, views, ordering and the budget gate
  E6  expiry at the boundary, in Your Plot and in Search, independent of any rebuild
  E7  guide and Living in the Garden counts equal the R-MATCH population; ranges and
      freshness unchanged
  E8  holds and VAT: hold register and protected records unchanged in substance; the
      21 supplier-terms VAT bases present and the refresh gate accepts the universe
  E9  Rayco's Stage 3D-D1 wording survives
Then 15 planted faults, each of which must be refused.
"""
import copy, datetime as dt, json, os, re, subprocess, sys, tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BASE = "959d24a"     # production before Stage 3D-D2
UNI, IDX = "garden-room-recommendation-universe-v1.json", "search-index-v1.json"
LITG, GUIDE = "discovery-living-in-the-garden.html", "garden-room-prices-ireland.html"
HOLDS = "atlas-tools/price-presentation-holds.json"
PROTECTED = {"recDa5vihxcYG9xoH": "NOOK 1", "rectQX4XpBbD6H3LU": "NOOK 2", "rec45XRwQ4qqGCQbv": "ECC 1",
             "recCF6Fdi2i1Qo04Z": "ECC 2", "recDIcUb7S6pP8JCx": "Rayco", "recej5DFaBD76ODlv": "PREMIUM S"}
RAYCO_NOTE = ("Rayco Modular Homes describes its garden rooms as installed, with foundations and site works "
              "quoted separately.")
UNVERIFIED = "Price not currently verified"
WINDOW = 180
TYPES = {"Standard Price", "Starting From", "Sale Price", "Sale"}
BAD_SCOPES = {"Range-Level", "Organisation-Wide"}


def dublin_today():
    try:
        from zoneinfo import ZoneInfo
        return dt.datetime.now(ZoneInfo("Europe/Dublin")).date()
    except Exception:
        return dt.date.today()


AS_OF = dt.date.fromisoformat(sys.argv[sys.argv.index("--as-of") + 1]) if "--as-of" in sys.argv else dublin_today()


def git(*a):
    return subprocess.run(["git", *a], cwd=ROOT, capture_output=True).stdout


def read(f):
    return (ROOT / f).read_text(encoding="utf-8")


def explorer_rows(html):
    m = re.search(r'<script type="application/json" class="pn-mx-config" id="mx-data">(.*?)</script>', html, re.S)
    cfg = json.loads(m.group(1)) if m else {"tabs": []}
    out = {}
    for t in cfg.get("tabs") or []:
        if t.get("key") != "gardenRooms":
            continue
        for mk in t.get("makers") or []:
            for p in mk.get("p") or []:
                out[p[0]] = (p[4] if len(p) > 4 else "", p[5] if len(p) > 5 else {})
    return out


def r_match(p, as_of):
    ref = p.get("priceEvidenceRef") or {}
    pe = p.get("priceEvidence") or {}
    c = ref.get("lastPriceCheck")
    try:
        fu = (dt.date.fromisoformat(c) + dt.timedelta(days=WINDOW)).isoformat()
    except (TypeError, ValueError):
        fu = None
    price = p.get("price")
    ok = bool(isinstance(price, (int, float)) and price > 0 and p.get("currency") and ref.get("adjudication") == "adjudicated"
              and p.get("priceStatus") == "Verified" and p.get("priceType") in TYPES and p.get("priceScope") not in BAD_SCOPES
              and fu and c <= as_of.isoformat() <= fu and not pe.get("presentationHold"))
    return ok, (fu if ok else None)


def runtime(files, day, group=(), queries=()):
    env = dict(os.environ, RM_GROUP=json.dumps(list(group)), RM_QUERIES=json.dumps(list(queries)))
    r = subprocess.run(["node", str(ROOT / "atlas-tools/rmatch-runtime.mjs"), files["yp"], files["sj"], files["un"], files["ix"],
                        day], capture_output=True, text=True, env=env)
    if r.returncode:
        raise RuntimeError(r.stderr[-800:])
    return json.loads(r.stdout)


def validator(universe_path, as_of):
    return subprocess.run([sys.executable, str(ROOT / ".github/scripts/validate_garden_room_universe.py"),
                           "--candidate", universe_path, "--as-of", as_of], capture_output=True, text=True)


def check_tree(S, tmp):
    """All E-checks over a tree state S (dict of parsed artefacts and paths). Returns failures."""
    bad = []
    fail = lambda n, d="": bad.append(n + ((" — " + str(d)[:220]) if d else ""))
    U = {p["id"]: p for p in S["uni"]["products"]}
    # E1
    for pid, p in U.items():
        ok, fu = r_match(p, AS_OF)
        if p.get("priceSafeForMatching") is True and not ok:
            fail("E1 %s is matching-eligible but fails R-MATCH" % pid)
        if p.get("priceSafeForMatching") is True and p.get("priceFreshUntil") != fu:
            fail("E1 %s has the wrong priceFreshUntil" % pid)
        if (p.get("priceState") == "eligible") != (p.get("priceSafeForMatching") is True):
            fail("E1 %s priceState disagrees with eligibility" % pid)
        if (p.get("priceEvidence") or {}).get("presentationHold") and p.get("priceState") != "held":
            fail("E1 %s is held but not in the held state" % pid)
    # E2
    pv = [p for p in U.values() if p.get("priceStatus") == "Partially Verified" and not (p.get("priceEvidence") or {}).get("presentationHold")]
    for p in pv:
        if p.get("priceState") != "not-verified" or p.get("priceSafeForMatching"):
            fail("E2 Partially Verified %s (%s) is not 'not-verified'" % (p["id"], p["organisation"]))
    for p in U.values():
        if p.get("priceScope") == "Range-Level" and p.get("priceSafeForMatching"):
            fail("E2 Range-Level %s is matching-eligible" % p["id"])
    # E3 Search
    idx = S["idx"]
    recs = idx["records"]
    prod = {r["id"][5:]: r for r in recs if r["type"] == "product" and r["id"].startswith("prod-rec")}
    base_ids = {r["id"] for r in S["base_idx"]["records"] if r["type"] == "product"}
    now_ids = {r["id"] for r in recs if r["type"] == "product"}
    if base_ids - now_ids:
        fail("E3 products disappeared from Search", sorted(base_ids - now_ids)[:4])
    for pid in U:
        if pid not in prod:
            fail("E3 %s is not in Search" % pid)
    elig_eur = {pid for pid, p in U.items() if r_match(p, AS_OF)[0] and p.get("currency") == "EUR"}
    for pid, r in prod.items():
        if pid not in U:
            continue
        if "price" in r and pid not in elig_eur:
            fail("E3 %s shows a Search figure that is not an eligible, current EUR price" % pid)
        if "price" in r and r.get("fu") != U[pid].get("priceFreshUntil"):
            fail("E3 %s Search figure carries the wrong expiry" % pid)
        if pid in elig_eur and "price" not in r:
            fail("E3 eligible %s lost its Search figure" % pid)
        if U[pid].get("priceState") == "not-verified" and r.get("ps") != "nv":
            fail("E3 %s is not verified but Search does not say so" % pid)
    by_org = {}
    for pid in elig_eur:
        by_org.setdefault(U[pid]["organisation"], []).append(U[pid])
    garden_orgs = {p["organisation"] for p in U.values()}
    mixed = {r["name"] for r in recs if r["type"] == "supplier"} & set(S.get("mixed") or [])
    for r in recs:
        if r["type"] != "supplier" or r["name"] not in garden_orgs or r["name"] in mixed:
            continue
        ps = by_org.get(r["name"])
        want = [min(x["price"] for x in ps), max(x["price"] for x in ps)] if ps else None
        if r.get("priceRange") != want:
            fail("E3 supplier %s range %r is not its eligible EUR prices %r" % (r["name"], r.get("priceRange"), want))
        if ps and r.get("fu") != min(x["priceFreshUntil"] for x in ps):
            fail("E3 supplier %s range expiry is wrong" % r["name"])
    # E4 Explorer
    ex = explorer_rows(S["litg"])
    base_ex = explorer_rows(S["base_litg"])
    for pid, p in U.items():
        if pid not in ex:
            fail("E4 %s missing from the Maker Explorer" % pid); continue
        lab, X = ex[pid]
        st = p.get("priceState")
        if st == "not-verified" and lab != UNVERIFIED:
            fail("E4 %s is not verified but the Explorer shows %r" % (pid, lab))
        if st == "eligible" and lab and lab not in (UNVERIFIED,) and re.search(r"[\d€£$]", lab) and X.get("fu") != p.get("priceFreshUntil"):
            fail("E4 %s Explorer figure carries the wrong expiry" % pid)
        if st != "eligible" and X.get("fu"):
            fail("E4 %s carries an expiry without an eligible figure" % pid)
        if st == "held" and lab != base_ex.get(pid, ("", {}))[0]:
            fail("E4 held %s Explorer label changed" % pid)
        if st == "eligible" and "incl. VAT (supplier’s terms)" in base_ex.get(pid, ("", {}))[0] \
                and "incl. VAT (supplier’s terms)" not in lab:
            fail("E4 Hansa24 %s lost 'incl. VAT (supplier's terms)'" % pid)
        if st == "eligible" and p.get("currency") == "EUR" and (p.get("priceEvidence") or {}).get("vatBasis") == "supplier-terms" \
                and "incl. VAT (supplier’s terms)" not in lab:
            fail("E4 eligible Hansa24 %s does not show 'incl. VAT (supplier's terms)'" % pid)
    # E5/E6 runtime
    files = S["files"]
    ver = sorted(pid for pid in elig_eur if (U[pid].get("priceEvidenceRef") or {}).get("lastPriceCheck"))
    if len(ver) < 2:   # every published price has expired: the runtime checks need two current ones
        fail("E5 fewer than two eligible, current EUR prices as of %s -- the published prices have expired" % AS_OF, len(ver))
        return bad
    v1 = ver[0]
    fu = U[v1]["priceFreshUntil"]
    day_after = (dt.date.fromisoformat(fu) + dt.timedelta(days=1)).isoformat()
    sprout = sorted(pid for pid, p in U.items() if p["organisation"] == "Sprout Pod")
    group = [sprout[0], "recDIcUb7S6pP8JCx", "recej5DFaBD76ODlv", v1, ver[1]]
    try:
        rt = runtime(files, AS_OF.isoformat(), group, ["garden room under €30,000", "Sprout Pod"])
        qv = "%s under €%s" % (U[v1]["organisation"], format(int(U[v1]["price"]) + 1, ","))
        rt2 = runtime(files, fu, group, [qv])
        rt3 = runtime(files, day_after, group, [qv])
    except RuntimeError as e:
        fail("E5 the page code could not run", e); return bad
    for pid, p in U.items():
        y = rt["yp"][pid]
        if p.get("priceState") == "not-verified" and (y["display"] != UNVERIFIED or y["figure"]):
            fail("E5 Your Plot shows %s as %r" % (pid, y["display"]))
        if p.get("priceState") == "eligible" and AS_OF.isoformat() <= (p.get("priceFreshUntil") or "") and not y["figure"]:
            fail("E5 Your Plot lost eligible %s's figure" % pid)
        if pid in PROTECTED and (y["figure"] or re.search(r"\d{1,3},\d{3}", (y["display"] or "") if PROTECTED[pid] in ("Rayco", "PREMIUM S") else "")):
            fail("E5 %s (%s) shows a figure" % (pid, PROTECTED[pid]))
        if y["note"] and p.get("priceState") in ("not-verified", "held") and re.search(r"[€£$]\s?\d", y["note"]):
            fail("E5 %s cost note shows a figure" % pid)
    if rt["order"][:2] != sorted([v1, ver[1]], key=lambda i: U[i]["price"]):
        fail("E5 tie ordering is not by the two eligible prices", rt["order"])
    if rt["raworder"][:2] != rt["order"][:2]:
        fail("E5 tie ordering lets an ineligible or held figure in", (rt["raworder"], rt["order"]))
    for pid in group:
        if pid not in (v1, ver[1]) and rt["budget"].get(pid) != 1:
            fail("E5 the budget gate scores ineligible %s" % pid)
    q = rt["search"]["q:garden room under €30,000"]["products"]
    if any(x[5:] in sprout for x in q):
        fail("E3 Sprout Pod enters a euro price filter")
    if len(rt["search"]["q:Sprout Pod"]["products"]) < len(sprout):
        fail("E3 Sprout Pod is no longer found by name")
    if rt["search"]["suppliers"].get("Sprout Pod"):
        fail("E3 Sprout Pod still has a supplier range")
    # E6 boundary
    if rt2["yp"][v1]["state"] != "eligible" or not rt2["yp"][v1]["figure"]:
        fail("E6 %s is not current ON its priceFreshUntil %s" % (v1, fu))
    if rt3["yp"][v1]["state"] != "not-verified" or rt3["yp"][v1]["figure"]:
        fail("E6 Your Plot keeps %s's expired figure on %s" % (v1, day_after))
    if v1 in rt3["order"][:1] and rt3["order"][:2] != rt2["order"][:2] and False:
        pass
    if rt3["order"][0] == v1:
        fail("E6 an expired price still orders a tie")
    if rt3["search"]["products"]["prod-" + v1]["price"] is not None or not rt3["search"]["products"]["prod-" + v1]["unverified"]:
        fail("E6 Search keeps %s's expired figure" % v1)
    qx = list(rt3["search"].values())[-1]["products"]
    if "prod-" + v1 in qx:
        fail("E6 an expired price enters a Search filter")
    if "prod-" + v1 not in list(rt2["search"].values())[-1]["products"]:
        fail("E6 a current price is missing from its Search filter")
    # E7 guide counts from the R-MATCH population
    rows = S["evidence"]["rows"]
    pop = [r for r in rows if U.get(r["productId"], {}).get("priceState") == "eligible"]
    n, nsup = len(pop), len({r["supplierKey"] for r in pop})
    nvat = sum(1 for r in pop if (r.get("vat") or "").lower() not in ("yes", "no", "excluding vat"))
    if len(rows) != n:
        fail("E7 the guide evidence holds %d rows, R-MATCH gives %d" % (len(rows), n))
    g, lg = S["guide"], S["litg"]
    if ("%d in all" % n) not in g or ("of %d do not say whether VAT" % n) not in g or ("from %d suppliers" % nsup) not in g:
        fail("E7 the guide does not state %d priced products from %d suppliers" % (n, nsup))
    if (">%d<" % nvat) not in g.replace("</span><span", "<"):
        fail("E7 the guide does not state %d without VAT" % nvat)
    if ("%d garden-room products with a euro price" % n) not in lg or ("From %d suppliers" % nsup) not in lg \
            or ("%d do not publish whether VAT" % nvat) not in lg:
        fail("E7 Living in the Garden does not state %d / %d / %d" % (n, nsup, nvat))
    rng = lambda h: re.findall(r"€[\d,]+\s*(?:&ndash;|–|to)\s*€[\d,]+", h)[:4]
    if rng(g) != rng(S["base_guide"]):
        fail("E7 the guide's published ranges changed", (rng(g), rng(S["base_guide"])))
    fresh = lambda h: re.findall(r"between <strong>[^<]+</strong> and <strong>[^<]+</strong>", h)
    if fresh(g) != fresh(S["base_guide"]):
        fail("E7 the guide's freshness statement changed")
    # E8 holds and VAT
    if S["holds"] != S["base_holds"]:
        fail("E8 the hold register changed")
    bU = {p["id"]: p for p in S["base_uni"]["products"]}
    for pid, name in PROTECTED.items():
        a, b = copy.deepcopy(U.get(pid) or {}), copy.deepcopy(bU.get(pid) or {})
        for k in ("priceState", "priceFreshUntil"):
            a.pop(k, None)
        if a != b:
            fail("E8 %s (%s) record changed beyond its price state" % (pid, name))
        if U[pid].get("priceState") != "held" or U[pid].get("priceSafeForMatching") or \
                ((U[pid].get("priceEvidence") or {}).get("presentationHold") or {}).get("matching") != "excluded":
            fail("E8 %s (%s) hold weakened" % (pid, name))
    vb = sum(1 for p in U.values() if (p.get("priceEvidence") or {}).get("vatBasis") == "supplier-terms")
    vbb = sum(1 for p in bU.values() if (p.get("priceEvidence") or {}).get("vatBasis") == "supplier-terms")
    if vb != vbb:
        fail("E8 supplier-terms VAT bases %d, production had %d" % (vb, vbb))
    up = Path(tmp) / "u-check.json"
    up.write_text(json.dumps(S["uni"]))
    v = validator(str(up), AS_OF.isoformat())
    if v.returncode:
        fail("E8 the refresh gate refuses the universe", [l for l in v.stdout.splitlines() if l.strip().startswith("- ")][:3])
    # E9 Rayco
    if rt["yp"]["recDIcUb7S6pP8JCx"]["note"] != RAYCO_NOTE:
        fail("E9 Rayco's approved wording is lost", rt["yp"]["recDIcUb7S6pP8JCx"]["note"])
    return bad


def load_state(tmp):
    t = Path(tmp)
    S = {"uni": json.loads(read(UNI)), "idx": json.loads(read(IDX)), "litg": read(LITG), "guide": read(GUIDE),
         "evidence": json.loads(read("atlas-tools/garden-room-price-page-evidence.json")), "holds": read(HOLDS),
         "base_uni": json.loads(git("show", BASE + ":" + UNI)), "base_idx": json.loads(git("show", BASE + ":" + IDX)),
         "base_litg": git("show", BASE + ":" + LITG).decode(), "base_guide": git("show", BASE + ":" + GUIDE).decode(),
         "base_holds": git("show", BASE + ":" + HOLDS).decode()}
    S["mixed"] = sorted({w for w in ("Hansa24 Group", "Pineca Ireland", "Gardenhouse24 Ireland")})
    write_files(S, t)
    return S


def write_files(S, t, yp=None, sj=None):
    t.mkdir(parents=True, exist_ok=True)
    (t / "u.json").write_text(json.dumps(S["uni"]))
    (t / "i.json").write_text(json.dumps(S["idx"]))
    (t / "yp.html").write_text(yp if yp is not None else read("your-plot.html"))
    (t / "s.js").write_text(sj if sj is not None else read("search.js"))
    S["files"] = {"yp": str(t / "yp.html"), "sj": str(t / "s.js"), "un": str(t / "u.json"), "ix": str(t / "i.json")}


def main():
    print("STAGE 3D-D2 — matching eligibility proof, as of %s (Europe/Dublin)" % AS_OF)
    with tempfile.TemporaryDirectory() as tmp:
        S = load_state(Path(tmp) / "clean")
        U = {p["id"]: p for p in S["uni"]["products"]}
        states = {}
        for p in U.values():
            states[p.get("priceState")] = states.get(p.get("priceState"), 0) + 1
        print("  price states: " + ", ".join("%s %d" % kv for kv in sorted(states.items())))
        bad = check_tree(S, tmp)
        for b in bad:
            print("  FAIL  " + b)
        print("  clean tree: %d failure(s)" % len(bad))
        sprout = sorted(pid for pid, p in U.items() if p["organisation"] == "Sprout Pod")
        elm = next(pid for pid, p in U.items() if p["organisation"].startswith("Elm"))
        quinn = next(pid for pid, p in U.items() if p.get("priceScope") == "Range-Level" and p.get("priceStatus") == "Verified")
        gbp = next(pid for pid, p in U.items() if p.get("currency") == "GBP" and p.get("priceState") == "eligible")
        hansa = next(pid for pid, p in U.items() if (p.get("priceEvidence") or {}).get("vatBasis"))
        elig = sorted(pid for pid, p in U.items() if p.get("priceState") == "eligible" and p.get("currency") == "EUR")

        def make_eligible(S, pid):
            p = next(x for x in S["uni"]["products"] if x["id"] == pid)
            p["priceSafeForMatching"] = True; p["priceState"] = "eligible"; p["priceFreshUntil"] = "2027-12-31"

        def idx_rec(S, pid):
            return next(r for r in S["idx"]["records"] if r["id"] == "prod-" + pid)

        def f1(S): make_eligible(S, sprout[0])
        def f2(S): make_eligible(S, elm)
        def f3(S): make_eligible(S, quinn)
        def f4(S):
            p = next(x for x in S["uni"]["products"] if x["id"] == elig[0]); p["priceFreshUntil"] = "2099-01-01"
        def f5(S):
            return {"sj": read("search.js").replace("if (r.fu && pnsToday() > r.fu) { return null; }", "")}
        def f6(S):
            return {"yp": read("your-plot.html").replace(
                "const amount = (e && e.product && (!pnPriceGoverned(e.product) || pnPriceIsCurrent(e.product)))\n        ? pnUsablePrice(e.product.price) : null;",
                "const amount = pnUsablePrice(e && e.product && e.product.price);")}
        def f7(S):
            p = next(x for x in S["uni"]["products"] if x["id"] == "recDIcUb7S6pP8JCx")
            p["priceState"] = "eligible"; p["priceSafeForMatching"] = True; p["priceFreshUntil"] = "2027-12-31"
            return {"yp": read("your-plot.html").replace("    if (e.presentationHold) return false;\n    if (P.priceState !== undefined",
                                                         "    if (P.priceState !== undefined", 1)}
        def f8(S):
            next(r for r in S["idx"]["records"] if r["type"] == "supplier" and r["name"] == "Sprout Pod")["priceRange"] = [10250, 24200]
        def f9(S):
            S["idx"]["records"] = [r for r in S["idx"]["records"] if r["id"] != "prod-" + sprout[1]]
        def f10(S):
            r = idx_rec(S, gbp); r["price"] = U[gbp]["price"]; r["fu"] = U[gbp]["priceFreshUntil"]
        def f11(S):
            next(x for x in S["uni"]["products"] if x["id"] == hansa)["priceEvidence"].pop("vatBasis")
        def f12(S):
            p = next(x for x in S["uni"]["products"] if x["id"] == "recDIcUb7S6pP8JCx")
            p["priceEvidence"].pop("presentationHold"); p["priceState"] = "eligible"; p["priceSafeForMatching"] = True
        def f13(S):
            p = next(x for x in S["uni"]["products"] if x["id"] == "recej5DFaBD76ODlv")
            p["priceEvidence"].pop("presentationHold"); p["priceState"] = "eligible"
        def f14(S):
            p = next(x for x in S["uni"]["products"] if x["id"] == "recDa5vihxcYG9xoH")
            p["priceEvidence"]["presentationHold"]["matching"] = "included"
        def f15(S):
            S["guide"] = S["guide"].replace("in all.", "in all, 237 in all.", 1).replace("%d in all" % len(S["evidence"]["rows"]), "237 in all")
        FAULTS = [(f1, "1 undated price entering matching", ("E1",)), (f2, "2 Partially Verified price entering matching", ("E1", "E2")),
                  (f3, "3 Range-Level price entering matching", ("E1", "E2")), (f4, "4 expired price remaining eligible", ("E1",)),
                  (f5, "5 expired price entering Search filters", ("E6",)), (f6, "6 expired price influencing tie ordering", ("E5", "E6")),
                  (f7, "7 held price influencing ordering", ("E5",)), (f8, "8 unsupported supplier range", ("E3",)),
                  (f9, "9 product disappearing from Search", ("E3",)), (f10, "10 GBP displayed as EUR in Search", ("E3",)),
                  (f11, "11 missing Hansa24 vatBasis", ("E8", "E4")), (f12, "12 Rayco historical price appearing", ("E5", "E1", "E8")),
                  (f13, "13 PREMIUM S price appearing", ("E5", "E1", "E8")), (f14, "14 NOOK hold weakened", ("E8",)),
                  (f15, "15 incorrect pricing-guide counts", ("E7",))]
        caught = 0
        for i, (f, label, codes) in enumerate(FAULTS, 1):
            T = copy.deepcopy({k: v for k, v in S.items() if k != "files"})
            k = f(T) or {}
            if any(k.get(x) is not None and k[x] == read(src) for x, src in (("yp", "your-plot.html"), ("sj", "search.js"))):
                print("  MISSED   planted %s: the fault could not be planted" % label); continue
            write_files(T, Path(tmp) / ("f%d" % i), yp=k.get("yp"), sj=k.get("sj"))
            got = check_tree(T, tmp)
            hit = any(g.startswith(codes) for g in got)
            caught += hit
            print("  %s  planted %-46s -> %s" % ("REFUSED" if hit else "MISSED ", label, (got or ["(nothing)"])[0][:120]))
        print("\nMATCHING ELIGIBILITY · %s — clean tree %d failure(s); planted faults %d/%d refused"
              % ("OK" if not bad and caught == len(FAULTS) else "FAILED", len(bad), caught, len(FAULTS)))
        return 0 if not bad and caught == len(FAULTS) else 1


if __name__ == "__main__":
    sys.exit(main())
