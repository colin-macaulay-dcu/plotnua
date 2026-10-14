#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
DISCOVERY MAKER SYNCHRONISATION — ONE LAYER OVER THE EXISTING PIPELINE.

Founder brief "Automatic Discovery Maker Synchronisation · permanent platform
capability" (14 Oct 2026). Adding an eligible product to Atlas should not
require editing every relevant Discovery by hand.

WHERE THIS SITS (nothing upstream of the published universes is touched)

  ATLAS RECORD ─ generators (.github/scripts/generate_*.py) and
      │          atlas-tools/publish-targeted-update.py: evidence validation,
      │          qualification, holds, the publication gate, image rights
      ▼
  PUBLISHED UNIVERSES  garden-room / additional-home / wellness (+ the two
      │                provider universes, organisation-only)
      ▼   ─────────────── THIS TOOL FROM HERE DOWN ───────────────
  DISCOVERY REGISTRY   which Discovery shows which Atlas Product Category,
      │                through which universe, in which explorer tab
      ▼
  MAKER EXPLORERS      rebuilt by build-maker-explorer.py's own build()
      ▼
  SEARCH INDEX         rebuilt by build-search-index.py
      ▼
  COUNTS + SNAPSHOT    derived; compared with the last publication snapshot

It never reads Airtable, never decides eligibility, never grants an image and
never publishes a record the universe does not already mark public. Eligibility
is read ONLY through the Maker Explorer's own source readers (SOURCES[...]
["read"]), so there is one rule, not two.

THE REGISTRY (REGISTRY below) reuses existing identifiers: the Search index's
possibility ids (poss-...), the Discovery routes, the Atlas Product Category
values, and the Maker Explorer's tab configuration (PAGES), which it does not
copy: guard S1 proves the two agree. A Discovery may draw on several
categories, and one universe may feed several Discoveries; a product shown in
two places is ONE canonical record in the snapshot, listed with every place it
appears ("in").

MODES
  --report [--out FILE]   dry run: verify, then the change report against the
                          last publication snapshot. Writes nothing (except FILE).
  --check                 verify, and fail if anything is pending publication.
  --apply --discovery ID [--discovery ID ...]
                          TARGETED: rebuild only these Discoveries' explorers,
                          then Search if a public record changed, then the
                          snapshot. REFUSES if another Discovery has pending
                          changes (Search is site-wide, so it would carry them).
  --apply --baseline      record the current published state as the snapshot;
                          refuses unless S1-S7 pass, writes nothing else.
  --apply --all           FULL regeneration: every explorer, Search, snapshot.
                          Use only when the founder has approved it.
  Never commits, pushes, deploys, emails or schedules anything.

VERIFICATION (every mode)
  S1 registry == Maker Explorer PAGES (same pages, same sources); every Atlas
     Product Category is either routed through a universe or declared UNROUTED
  S2 category integrity: every record of a universe carries that universe's
     Atlas Product Category (a mismatch is held for review, never published)
  S3 each maker-explorer page is exactly what its builder writes now
  S4 provider explorers pass their own --check
  S5 Search parity: per universe, the products Search lists == the products
     the explorers list, apart from Search's own declared exception (R3, below)
  S6 no held or ineligible product appears on any explorer page or in Search
  S7 product links: a PlotNua product page resolves to a listed product; a
     wellness route lands on the Garden Retreat explorer that lists it; a
     maker link is VERIFIED in maker-product-links-v1.json
"""
import hashlib
import importlib.util
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
TOOLS = ROOT / "atlas-tools"
SNAPSHOT = TOOLS / "discovery-maker-snapshot-v1.json"
SEARCH = ROOT / "search-index-v1.json"

# ───────────────────────────────────────────────────────────── the registry ──
# One row per Discovery that shows makers or providers. "categories" are Atlas
# Product Category values (Products.Product Category, an explicit governed
# single-select), never inferred from names or keywords.
REGISTRY = [
    {"id": "poss-living-in-the-garden", "route": "discovery-living-in-the-garden.html",
     "explorer": "maker", "categories": ["Garden Rooms", "Additional Home"], "search": True},
    {"id": "poss-garden-retreat", "code": "DISC-001", "route": "discovery-garden-retreat.html",
     "explorer": "maker", "categories": ["Wellness / Sauna"], "search": True},
    {"id": "poss-the-borrowed-garden", "code": "DISC-025", "route": "discovery-the-borrowed-garden.html",
     "explorer": "provider", "categories": [], "search": False,
     "universe": "borrowed-garden-provider-universe-v1.json",
     "builder": "atlas-tools/build-provider-explorer.py"},
    {"id": "poss-house-as-power-station", "code": "DISC-026", "route": "discovery-house-as-power-station.html",
     "explorer": "provider", "categories": [], "search": False,
     "universe": "power-station-provider-universe-v1.json",
     "builder": "atlas-tools/build-power-station-provider-explorer.py"},
]
# The Atlas Product Category each published product universe is generated from.
SOURCE_CATEGORY = {
    "garden-room-universe-v1": "Garden Rooms",
    "additional-home-universe-v1": "Additional Home",
    "wellness-universe-v1": "Wellness / Sauna",
}
# Atlas Product Category choices with NO generator, NO qualification rule and
# NO Discovery mapping (Atlas read-back, 14 Oct 2026: 1,242 products, 374 of
# them in these categories). Publishing any of them needs its own eligibility
# rule and a founder decision; nothing here maps them by guesswork.
UNROUTED_CATEGORIES = ["Carports", "Garages", "Garden Storage", "Greenhouses", "Guest Accommodation",
                       "Homes", "Log Cabins", "Steel Sheds", "Summerhouses", "Timber Sheds", "Treehouses"]
# Search's declared exception (build-search-index.py, "AH withheld", rule R3):
# an Additional Home product whose maker already has a Garden Room supplier
# record is listed by the explorer but withheld from Search, so the supplier
# corpus is not re-aggregated. Recognised here, never widened.
SEARCH_EXCEPTION = "additional-home-universe-v1: maker already has a Garden Room supplier record (Search R3)"


def die(msg):
    print("REFUSED: " + msg)
    sys.exit(2)


def _load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


ME = _load_module("build_maker_explorer", TOOLS / "build-maker-explorer.py")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def reg(rid):
    for r in REGISTRY:
        if r["id"] == rid:
            return r
    die("no Discovery %r in the registry (known: %s)" % (rid, ", ".join(r["id"] for r in REGISTRY)))


# ─────────────────────────────────────────────────────────────── the state ──
def state():
    """The published Discovery state, derived ONLY through the explorer's own
    readers. Deterministic: sorted keys, no timestamps."""
    sources, products, discoveries, problems = {}, {}, {}, []
    universes = {}
    for key, S in ME.SOURCES.items():
        U = json.loads((ROOT / S["file"]).read_text(encoding="utf-8"))
        universes[key] = U
        eligible, held, orgs, _ = S["read"](U)
        cat = SOURCE_CATEGORY.get(key)
        for q in U["products"]:                                   # S2
            if q.get("productCategory") != cat:
                problems.append("S2 %s record %s carries Product Category %r, not %r; held for review"
                                % (key, q.get("id"), q.get("productCategory"), cat))
        sources[key] = {"file": S["file"], "sha256": sha(ROOT / S["file"]), "category": cat,
                        "published": len(eligible), "held": len(held),
                        "makers": len({e[0] for e in eligible})}
    for R in REGISTRY:
        D = {"route": R["route"], "explorer": R["explorer"], "categories": R["categories"], "tabs": {}}
        if R["explorer"] == "maker":
            tabs, researched, held = ME.load(ME.PAGES[R["route"]])
            ids, makers = set(), set()
            for t in tabs:
                T, cfg = t["T"], t["cfg"]
                D["tabs"][T["key"]] = {"source": T["source"], "products": cfg["figures"]["products"],
                                       "makers": cfg["figures"]["makers"]}
                for m in cfg["makers"]:
                    makers.add(m["m"])
                    for row in m["p"]:
                        pid = row[0]
                        nav = row[5] if len(row) > 5 else {}
                        rec = {"maker": m["m"], "name": row[1], "type": row[2], "irish": row[3],
                               "price": row[4] if len(row) > 4 else "", "source": T["source"],
                               "link": nav.get("href") or "",
                               "images": sorted(i["src"] for i in nav.get("img") or [])}
                        prev = products.get(pid)
                        if prev and {k: v for k, v in prev.items() if k != "in"} != rec:
                            problems.append("canonical record %s differs between placements" % pid)
                        products.setdefault(pid, dict(rec, **{"in": []}))
                        products[pid]["in"].append("%s#%s" % (R["id"], T["key"]))
                        ids.add(pid)
            # deduplicated: a dual-use product in two tabs counts once
            D.update({"products": len(ids), "makers": len(makers), "researchedMakers": researched,
                      "held": sorted(held)})
        else:
            U = json.loads((ROOT / R["universe"]).read_text(encoding="utf-8"))
            for t in U["tabs"]:
                D["tabs"][t["key"]] = {"organisations": sorted(o["code"] for o in t["orgs"])}
            D["organisations"] = len({o["code"] for t in U["tabs"] for o in t["orgs"]})
            D["universeSha256"] = sha(ROOT / R["universe"])
        discoveries[R["id"]] = D
    for p in products.values():
        p["in"].sort()
    return {"schema": "plotnua.discovery-maker-sync", "version": "1",
            "sources": sources, "discoveries": discoveries,
            "products": dict(sorted(products.items())),
            "coverage": {"routed": {SOURCE_CATEGORY[k]: k for k in SOURCE_CATEGORY},
                         "unrouted": UNROUTED_CATEGORIES},
            "searchException": SEARCH_EXCEPTION}, problems, universes


def dump(s):
    return json.dumps(s, indent=1, ensure_ascii=False, sort_keys=True) + "\n"


# ──────────────────────────────────────────────────────────── verification ──
def search_products():
    S = json.loads(SEARCH.read_text(encoding="utf-8"))
    return {r["id"][5:]: r for r in S["records"] if r["type"] == "product"}


def verify(st, problems, universes, pages=None):
    """Return a list of failures (empty = in sync)."""
    fails = list(problems)
    # S1 registry == explorer configuration; categories accounted for
    maker_routes = {r["route"] for r in REGISTRY if r["explorer"] == "maker"}
    if maker_routes != set(ME.PAGES):
        fails.append("S1 registry maker Discoveries %s != Maker Explorer pages %s"
                     % (sorted(maker_routes), sorted(ME.PAGES)))
    if set(SOURCE_CATEGORY) != set(ME.SOURCES):
        fails.append("S1 SOURCE_CATEGORY does not name exactly the explorer's published sources")
    if set(SOURCE_CATEGORY.values()) & set(UNROUTED_CATEGORIES):
        fails.append("S1 a category is both routed and unrouted")
    for R in REGISTRY:
        if R["explorer"] == "maker" and R["route"] in ME.PAGES:
            want = sorted({SOURCE_CATEGORY[T["source"]] for T in ME.PAGES[R["route"]]["tabs"]})
            if sorted(R["categories"]) != want:
                fails.append("S1 %s declares categories %r but its tabs draw on %r" % (R["id"], R["categories"], want))
    # S3 explorer pages up to date (the builder's own build(), all its guards)
    for R in REGISTRY:
        if R["explorer"] != "maker" or (pages and R["id"] not in pages):
            continue
        src = (ROOT / R["route"]).read_text(encoding="utf-8")
        try:
            if ME.build(R["route"], ME.PAGES[R["route"]], src) != src:
                fails.append("S3 %s is out of date with its universes" % R["route"])
        except SystemExit:
            fails.append("S3 %s: the Maker Explorer builder refused (see above)" % R["route"])
    # S4 provider explorers
    for R in REGISTRY:
        if R["explorer"] == "provider":
            r = subprocess.run([sys.executable, str(ROOT / R["builder"]), "--check"],
                               capture_output=True, text=True, cwd=str(ROOT))
            if r.returncode != 0:
                fails.append("S4 %s: %s" % (R["builder"], (r.stdout.strip().splitlines() or ["?"])[-1]))
    # S5 / S6 Search parity, no held product anywhere public
    sp = search_products()
    gr_orgs = {e[0] for e in ME.SOURCES["garden-room-universe-v1"]["read"](universes["garden-room-universe-v1"])[0]}
    for key, S in ME.SOURCES.items():
        eligible, held, _, _ = S["read"](universes[key])
        pub = {e[1] for e in eligible}
        allowed_gap = {e[1] for e in eligible if key == "additional-home-universe-v1" and e[0] in gr_orgs}
        in_search = pub & set(sp)
        if pub - in_search - allowed_gap:
            fails.append("S5 %s: %d published product(s) missing from Search, e.g. %s"
                         % (key, len(pub - in_search - allowed_gap), sorted(pub - in_search - allowed_gap)[:3]))
        if held & set(sp):
            fails.append("S6 %s: held product(s) in Search: %s" % (key, sorted(held & set(sp))[:5]))
    listed = set(st["products"])
    stray = set(sp) - listed - {e[1] for k in ME.SOURCES for e in ME.SOURCES[k]["read"](universes[k])[0]}
    if stray:
        fails.append("S6 Search lists %d product(s) no explorer source publishes, e.g. %s" % (len(stray), sorted(stray)[:3]))
    for R in REGISTRY:
        if R["explorer"] != "maker":
            continue
        html = (ROOT / R["route"]).read_text(encoding="utf-8")
        leak = [h for h in st["discoveries"][R["id"]]["held"] if h in html]
        if leak:
            fails.append("S6 %s shows held product(s): %s" % (R["route"], leak[:5]))
    # S7 links
    gr_pub = {e[1] for e in ME.SOURCES["garden-room-universe-v1"]["read"](universes["garden-room-universe-v1"])[0]}
    for pid, p in st["products"].items():
        page = ME.SOURCES[p["source"]]["productPage"]
        if page and pid not in gr_pub:
            fails.append("S7 %s links to %s, which does not resolve it" % (pid, page))
        if p["link"] and not ME.verified_link(pid, universes and _org_of(universes, p["source"], pid), p["link"]):
            fails.append("S7 %s carries a maker link that is not VERIFIED" % pid)
    for pid, r in sp.items():
        route = r.get("route") or ""
        m = re.fullmatch(r"(discovery-[a-z0-9-]+\.html)#p-(rec[A-Za-z0-9]{14})", route)
        if route and m:
            rid = [x["id"] for x in REGISTRY if x["route"] == m.group(1)]
            if m.group(2) != pid or not rid or not any(i.startswith(rid[0] + "#")
                                                       for i in st["products"].get(pid, {}).get("in", [])):
                fails.append("S7 Search routes %s to %s, which does not list it" % (pid, route))
    return fails


def _org_of(universes, key, pid):
    for q in universes[key]["products"]:
        if q.get("id") == pid:
            return q.get("organisation")
    return None


# ──────────────────────────────────────────────────────────── change report ──
def diff(old, new):
    """Reviewable publication diff, grouped as the founder brief lists it."""
    out = {k: [] for k in ("newMakers", "newProducts", "updatedProducts", "removedProducts", "newlyHeld",
                           "categoryChanges", "priceChanges", "imageRightsChanges", "countChanges",
                           "sourceChanges")}
    op, np_ = old.get("products", {}), new["products"]
    held_now = {h for D in new["discoveries"].values() for h in D.get("held", [])}
    for pid in sorted(set(np_) - set(op)):
        p = np_[pid]
        out["newProducts"].append("%s · %s · %s → %s" % (pid, p["maker"], p["name"], ", ".join(p["in"])))
    for pid in sorted(set(op) - set(np_)):
        p = op[pid]
        bucket = "newlyHeld" if pid in held_now else "removedProducts"
        out[bucket].append("%s · %s · %s (was %s)" % (pid, p["maker"], p["name"], ", ".join(p["in"])))
    for pid in sorted(set(op) & set(np_)):
        a, b = op[pid], np_[pid]
        changed = [k for k in ("maker", "name", "type", "irish", "link") if a.get(k) != b.get(k)]
        if changed:
            out["updatedProducts"].append("%s · %s: %s" % (pid, b["name"], ", ".join(
                "%s %r → %r" % (k, a.get(k), b.get(k)) for k in changed)))
        if a.get("in") != b.get("in"):
            out["categoryChanges"].append("%s · %s: %s → %s" % (pid, b["name"], a.get("in"), b["in"]))
        if a.get("price") != b.get("price"):
            out["priceChanges"].append("%s · %s: %r → %r" % (pid, b["name"], a.get("price"), b["price"]))
        if a.get("images") != b.get("images"):
            out["imageRightsChanges"].append("%s · %s: %d → %d authorised image(s)"
                                             % (pid, b["name"], len(a.get("images") or []), len(b["images"])))
    od = old.get("discoveries", {})
    for rid, D in new["discoveries"].items():
        O = od.get(rid, {})
        old_makers = {op[p]["maker"] for p in op if any(i.startswith(rid + "#") for i in op[p]["in"])}
        new_makers = {np_[p]["maker"] for p in np_ if any(i.startswith(rid + "#") for i in np_[p]["in"])}
        for m in sorted(new_makers - old_makers):
            out["newMakers"].append("%s · %s" % (rid, m))
        for k in ("products", "makers", "organisations"):
            if k in D and O.get(k) != D[k]:
                out["countChanges"].append("%s %s: %s → %s" % (rid, k, O.get(k), D[k]))
        for tk, T in D["tabs"].items():
            OT = (O.get("tabs") or {}).get(tk, {})
            for k in ("products", "makers", "organisations"):
                if k in T and OT.get(k) != T[k]:
                    out["countChanges"].append("%s#%s %s: %s → %s" % (rid, tk, k, OT.get(k), T[k]))
    for k, S in new["sources"].items():
        if (old.get("sources", {}).get(k) or {}).get("sha256") != S["sha256"]:
            out["sourceChanges"].append("%s (%s) changed" % (k, S["file"]))
    return out


def pending_by_discovery(old, new):
    """Which Discoveries the diff touches."""
    touched = set()
    op, np_ = old.get("products", {}), new["products"]
    for pid in set(op) | set(np_):
        a, b = op.get(pid), np_.get(pid)
        if a != b:
            for i in (a or {}).get("in", []) + (b or {}).get("in", []):
                touched.add(i.split("#")[0])
    for rid, D in new["discoveries"].items():
        if old.get("discoveries", {}).get(rid) != D:
            touched.add(rid)
    return touched


def render(d, fails, touched, regen=()):
    lines = ["DISCOVERY MAKER SYNCHRONISATION — CHANGE REPORT", ""]
    titles = {"newMakers": "New eligible makers", "newProducts": "New eligible products",
              "updatedProducts": "Updated products", "removedProducts": "Removed products",
              "newlyHeld": "Newly held products", "categoryChanges": "Category / placement changes",
              "priceChanges": "Price changes", "imageRightsChanges": "Image-rights changes",
              "countChanges": "Changed Discovery counts", "sourceChanges": "Published universes changed"}
    for k, t in titles.items():
        lines.append("%s: %d" % (t, len(d[k])))
        lines += ["  - " + x for x in d[k][:40]] + (["  … %d more" % (len(d[k]) - 40)] if len(d[k]) > 40 else [])
    lines += ["", "Discoveries with pending changes: %s" % (", ".join(sorted(touched)) or "none")]
    if regen:
        lines += ["", "Awaiting regeneration (published by --apply):"] + ["  · " + f for f in regen]
    lines += ["", "Verification: %s" % ("PASS (S1-S7)" if not fails else "FAIL")] + ["  ✗ " + f for f in fails]
    return "\n".join(lines) + "\n"


# ──────────────────────────────────────────────────────────────── actions ──
def rebuild_search():
    """Rebuild Search with its own builder. If no RECORD changed, the committed
    bytes are kept (the builder stamps a time and commit on every run), so a
    repeated run with no Atlas change writes nothing."""
    before = SEARCH.read_bytes()
    r = subprocess.run([sys.executable, str(TOOLS / "build-search-index.py")],
                       capture_output=True, text=True, cwd=str(ROOT))
    if r.returncode != 0:
        SEARCH.write_bytes(before)
        die("the Search builder refused:\n" + r.stdout[-1500:])
    a, b = json.loads(before), json.loads(SEARCH.read_bytes())
    strip = lambda j: {k: v for k, v in j.items() if k not in ("generated", "sourceCommit")}
    if strip(a) == strip(b):
        SEARCH.write_bytes(before)
        return False
    return True


def main(argv):
    mode = next((m for m in ("--report", "--check", "--apply") if m in argv), "--report")
    targets = [argv[i + 1] for i, a in enumerate(argv) if a == "--discovery" and i + 1 < len(argv)]
    for t in targets:
        reg(t)
    st, problems, universes = state()
    old = json.loads(SNAPSHOT.read_text(encoding="utf-8")) if SNAPSHOT.exists() else {}
    if mode != "--apply":
        found = verify(st, problems, universes)
        # Before an apply, a page not yet rebuilt (S3) and a product not yet in
        # Search (S5) are the pending publication itself, not faults. Anything
        # else (a held product showing, a broken link, a category mismatch)
        # is a failure in every mode.
        regen = [f for f in found if f.startswith(("S3 ", "S5 ")) and "refused" not in f]
        fails = [f for f in found if f not in regen]
        d, touched = diff(old, st), pending_by_discovery(old, st)
        rep = render(d, fails, touched, regen)
        print(rep, end="")
        if "--out" in argv:
            pathlib.Path(argv[argv.index("--out") + 1]).write_text(rep, encoding="utf-8")
        if fails:
            sys.exit(2)
        if mode == "--check" and (touched or regen or not SNAPSHOT.exists()):
            print("CHECK FAILED: changes are pending publication (run --report to review)")
            sys.exit(1)
        print("IN SYNC" if not (touched or regen) else "PENDING: review the report, then --apply --discovery <id>")
        return
    # --apply
    if "--baseline" in argv:
        # Record the CURRENT published state as the publication snapshot.
        # Writes the snapshot only; refuses unless every page and Search
        # already match their universes (S1-S7), so nothing public moves.
        fails = verify(st, problems, universes)
        if fails:
            die("a baseline needs a site in sync:\n  " + "\n  ".join(fails))
        SNAPSHOT.write_text(dump(st), encoding="utf-8")
        print("BASELINE recorded: %s · %d products in %d Discoveries · nothing else written"
              % (SNAPSHOT.relative_to(ROOT), len(st["products"]), len(REGISTRY)))
        return
    if not targets and "--all" not in argv:
        die("--apply needs --discovery <id> (targeted) or --all (full regeneration, founder-approved)")
    if problems:
        die("held for review:\n  " + "\n  ".join(problems))
    touched = pending_by_discovery(old, st) if old else {r["id"] for r in REGISTRY}
    scope = {r["id"] for r in REGISTRY} if "--all" in argv else set(targets)
    others = touched - scope
    if others:
        die("other Discoveries have pending changes (%s). Search is site-wide and would publish them "
            "too: include them, use --all with founder approval, or hold their records first."
            % ", ".join(sorted(others)))
    written = []
    for R in REGISTRY:
        if R["id"] in scope and R["explorer"] == "maker":
            page = ROOT / R["route"]
            src = page.read_text(encoding="utf-8")
            out = ME.build(R["route"], ME.PAGES[R["route"]], src)
            if out != src:
                page.write_text(out, encoding="utf-8")
                written.append(R["route"])
    if any(reg(t)["search"] for t in scope) and rebuild_search():
        written.append(SEARCH.name)
    st2, problems2, universes2 = state()
    fails = verify(st2, problems2, universes2)
    if fails:
        die("verification failed after the rebuild (files left for inspection):\n  " + "\n  ".join(fails))
    rep = render(diff(old, st2), fails, touched & scope)
    text = dump(st2)
    if not SNAPSHOT.exists() or SNAPSHOT.read_text(encoding="utf-8") != text:
        SNAPSHOT.write_text(text, encoding="utf-8")
        written.append(str(SNAPSHOT.relative_to(ROOT)))
    print(rep, end="")
    if "--out" in argv:
        pathlib.Path(argv[argv.index("--out") + 1]).write_text(rep, encoding="utf-8")
    print("APPLIED (%s) · written: %s · nothing committed, pushed or deployed"
          % ("full" if "--all" in argv else "targeted: " + ", ".join(sorted(scope)), ", ".join(written) or "nothing"))


if __name__ == "__main__":
    main(sys.argv[1:])
