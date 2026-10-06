#!/usr/bin/env python3
"""PHASE 5 CANDIDATE GENERATOR — SHADOW ONLY.

Replaces the hard-coded dryRun/version pair with an explicit --mode, emits a
provenance block a consumer can check, computes a governed-field digest so any
post-generation mutation is detectable, and FAILS the production mode when
validation does not pass.

It never writes to Atlas, never touches your-plot.html, and never replaces the
operative universe. Output goes to phase5/ only.

SOURCE HONESTY: the evidence base is the operative artefact (the same rows the
live journey reads) PLUS source-corrections-v1.json, an explicit overlay whose
Power Sheds entries are real Atlas Product Pricing reads with record IDs. This
is a shadow source snapshot, NOT a live full-Airtable export; the limitation is
recorded in the provenance block as sourceKind.
"""
import argparse, hashlib, json, re, subprocess, sys, unicodedata
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent.parent                      # plotnua-github
OPERATIVE = ROOT / "garden-room-recommendation-universe-v1.json"
AXES = HERE.parent / "price-basis-axes-v1.json"
OVERLAY = HERE / "source-corrections-v1.json"
GENERATOR_VERSION = "2.0.0"

# ── the 13 governed fields, and the retired one ───────────────────────────
GOVERNED = ["priceRecordIds","priceRecordIdsAvailable","priceStatus","priceType",
            "priceScope","vatStatus","vatRate","priceBasisAxes","priceBasisClass",
            "priceBasisConfidence","priceIsRangeFloor","priceSafeForMatching",
            "priceEvidenceRef"]
RETIRED_FIELD = "priceBasis"
CLASSES = {"EX_WORKS","ERECTED_WITH_SERVICES","ERECTED_SERVICES_EXCLUDED",
           "ERECTED_SERVICES_UNKNOWN","DELIVERED_SHELL","KIT_SELF_ASSEMBLY","UNKNOWN"}
# IDENTICAL to Phase 4, so the candidate/Phase-4 comparison is not confounded.
UNSAFE_CONF = {"UNSAFE","CONFLICTED"}
# keys that would carry curator working notes; never copied onto a product
FORBIDDEN_KEYS = {"quote","note","notes","basisNotes","curatorNote","considerations","rationale"}

def derive(ax):
    e,d,s = ax.get("erection"),ax.get("delivery"),ax.get("siteWorks")
    if e=="EXCLUDED" and d=="EXCLUDED":  return "EX_WORKS"
    if e=="INCLUDED" and s=="INCLUDED":  return "ERECTED_WITH_SERVICES"
    if e=="INCLUDED" and s=="EXCLUDED":  return "ERECTED_SERVICES_EXCLUDED"
    if e=="INCLUDED" and s=="UNKNOWN":   return "ERECTED_SERVICES_UNKNOWN"
    if e=="EXCLUDED" and d=="INCLUDED":  return "DELIVERED_SHELL"
    if e=="EXCLUDED":                    return "KIT_SELF_ASSEMBLY"
    return "UNKNOWN"                               # fails closed

def fold(s):
    """IDENTICAL to build-shadow-universe.py. My first version used
       re.sub(r"[^a-z0-9]","") which DESTROYS accented characters rather than
       transliterating them, so 'OOD House' never matched 'ÖÖD House' and eight
       products silently lost their axes evidence. Diacritic-insensitive folding
       is the whole point of this function; it is copied, not re-derived."""
    if not s: return ""
    return "".join(c for c in unicodedata.normalize("NFKD", s)
                   if not unicodedata.combining(c)).strip().lower()

def governed_digest(products):
    """Digest over ONLY the governed fields, in a fixed order, so the proof is
       immune to unrelated churn elsewhere in the artefact."""
    h = hashlib.sha256()
    for p in sorted(products, key=lambda x: x.get("productId") or ""):
        h.update((p.get("productId") or "").encode())
        for k in GOVERNED:
            h.update(b"\x1f"); h.update(json.dumps(p.get(k), sort_keys=True, separators=(",",":")).encode())
        h.update(b"\x1e")
    return h.hexdigest()

def git(*a):
    try: return subprocess.run(["git","-C",str(ROOT),*a],capture_output=True,text=True,timeout=20).stdout.strip() or None
    except Exception: return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--verify", default=None,
                    help="recompute the governed digest of an existing artefact and compare "
                         "with its own declaration; exit 1 on mismatch. ONE canonical digest "
                         "implementation is used for both writing and verifying, so a second "
                         "implementation cannot drift away from it.")
    ap.add_argument("--mode", required=False, choices=["shadow","production"],
                    help="shadow = candidate for review; production = promotion, gated by validation")
    ap.add_argument("--out", default=None)
    a = ap.parse_args()

    if a.verify:
        art = json.loads(Path(a.verify).read_text())
        declared = art.get("governedDigest")
        global GOVERNED
        if art.get("governedFields"): GOVERNED = art["governedFields"]
        actual = governed_digest(art["products"])
        if declared == actual:
            print("INTEGRITY OK   %s  digest=%s" % (Path(a.verify).name, actual)); return
        print("INTEGRITY FAIL %s\n  declared=%s\n  recomputed=%s" % (Path(a.verify).name, declared, actual))
        raise SystemExit(1)

    if not a.mode: raise SystemExit("--mode is required unless --verify is used")
    base = json.loads(OPERATIVE.read_text())
    axes = json.loads(AXES.read_text())
    overlay = json.loads(OVERLAY.read_text())
    PRD = {fold(k):v for k,v in axes["byProduct"].items()}
    ORG = {fold(k):v for k,v in axes["byOrganisation"].items()}
    AX_UNKNOWN = {"erection":"UNKNOWN","siteWorks":"UNKNOWN","delivery":"UNKNOWN",
                  "confidence":"NO_EVIDENCE_RECORDED","quote":None}
    CORR = {c["productId"]:c for c in overlay["corrections"]}

    products, applied = [], []
    for p in base["products"]:
        q = dict(p)
        pid = q.get("productId")
        ev = dict(q.get("priceEvidence") or {})

        # ── source correction, applied BEFORE any derivation ───────────────
        c = CORR.get(pid)
        if c:
            # A WITHDRAWN price carries atlasBasePrice None: the row keeps its
            # record for provenance but stops being a governed number, exactly
            # as the live Atlas record now behaves.
            q["price"] = c["atlasBasePrice"]
            q["currency"] = c["atlasCurrency"]
            ev = {"base": c["atlasBasePrice"], "from": None, "to": c["atlasPriceTo"],
                  "currency": c["atlasCurrency"], "priceType": c["atlasPriceType"],
                  "status": c["atlasPriceStatus"], "includesVat": c["atlasIncludesVat"],
                  "evidenceScope": c.get("atlasEvidenceScope"), "adjudication": c["adjudication"],
                  "candidateCount": c["candidateCount"]}
            q["priceEvidence"] = ev
            applied.append(c["id"])

        # ── the 13 governed fields ────────────────────────────────────────
        rec_ids = c["priceRecordIds"] if c else []
        q["priceRecordIds"] = list(rec_ids)
        q["priceRecordIdsAvailable"] = bool(rec_ids)
        q["priceStatus"] = ev.get("status")
        q["priceType"] = (ev.get("priceType") or "").strip() or None
        q["priceScope"] = ev.get("evidenceScope")
        q["vatStatus"] = ev.get("includesVat")
        q["vatRate"] = None                      # never published anywhere in Atlas
        axv = PRD.get(fold(q.get("name"))) or ORG.get(fold(q.get("organisation"))) or AX_UNKNOWN
        q["priceBasisAxes"] = {"erection":axv["erection"],"siteWorks":axv["siteWorks"],
                               "delivery":axv["delivery"]}
        q["priceBasisClass"] = derive(q["priceBasisAxes"])
        if q["priceBasisClass"] not in CLASSES:
            raise SystemExit("REFUSED: derive() produced %r, outside the closed vocabulary" % q["priceBasisClass"])
        priced = isinstance(q.get("price"),(int,float)) and q["price"] > 0
        conf = axv["confidence"] if priced else "NO_PRICE"
        q["priceBasisConfidence"] = conf
        # Range floor: Phase 4's three governed shapes, PLUS a published
        # Price To that differs from Base Price, which the Power Sheds records
        # genuinely have (6129->6219, 6959->7044). No guessing.
        q["priceIsRangeFloor"] = bool(
            (ev.get("base") in (None,"") and ev.get("from") not in (None,""))
            or q["priceType"] == "Starting From"
            or (axv is not AX_UNKNOWN and conf == "PARTIAL" and q.get("organisation") == "Sprout Pod")
            or (ev.get("to") not in (None,"") and ev.get("to") != ev.get("base")))
        # Phase 4 safety, plus the new rule the Power Sheds forensic earned:
        # an ambiguous adjudication can never be matched, whatever it holds.
        q["priceSafeForMatching"] = bool(priced and conf not in UNSAFE_CONF
                                         and ev.get("adjudication") != "ambiguous")
        # Phase 4 carried axesFile/axesVersion on every ref. Dropping them was a
        # provenance REGRESSION caught by G10; both are restored and the new
        # record-level provenance is added beside them, not instead of them.
        q["priceEvidenceRef"] = {"axesFile": AXES.name, "axesVersion": axes["version"],
                                 "organisation": q.get("organisation"),
                                 "lastPriceCheck": ev.get("lastPriceCheck"),
                                 "productId": pid, "priceRecordIds": list(rec_ids),
                                 "adjudication": ev.get("adjudication"),
                                 "candidateCount": ev.get("candidateCount")}
        q.pop(RETIRED_FIELD, None)
        for k in FORBIDDEN_KEYS:
            if k in q: raise SystemExit("REFUSED: forbidden key %r reached the payload" % k)
        products.append(q)

    # ── validation ────────────────────────────────────────────────────────
    orgs = {p.get("organisation") for p in products if p.get("organisation")}
    checks = {
      "all_products_carry_13_fields": all(all(k in p for k in GOVERNED) for p in products),
      "retired_priceBasis_absent":    all(RETIRED_FIELD not in p for p in products),
      "basis_class_closed_vocabulary":all(p["priceBasisClass"] in CLASSES for p in products),
      "no_vat_rate_invented":         all(p["vatRate"] is None for p in products),
      "no_ambiguous_row_retains_price": all(
          not ((p.get("priceEvidence") or {}).get("adjudication")=="ambiguous" and p.get("price") is not None)
          for p in products),
      "derivation_exercises_axes":    len({p["priceBasisClass"] for p in products}) > 1,
      "safety_flag_not_inert":        any(p["priceSafeForMatching"] is False for p in products),
      "product_count_preserved":      len(products)==len(base["products"]),
    }
    ok = all(checks.values())

    out = {
      "generationMode": a.mode,
      "shadow": a.mode == "shadow",
      "notAuthorisedForRuntime": a.mode == "shadow",
      "basisAxesFile": AXES.name,
      "basisAxesVersion": axes["version"],
      "builtFrom": {"artefact": OPERATIVE.name, "generated": base.get("generated")},
      "generatorVersion": GENERATOR_VERSION,
      "generated": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
      "provenance": {
        "sourceKind": "shadow-source-snapshot (operative artefact + source-corrections-v1.json). NOT a live full-Airtable export.",
        "operativeArtefact": OPERATIVE.name,
        "operativeArtefactGenerated": base.get("generated"),
        "operativeArtefactSha256": hashlib.sha256(OPERATIVE.read_bytes()).hexdigest(),
        "axesFile": AXES.name,
        "axesFileSha256": hashlib.sha256(AXES.read_bytes()).hexdigest(),
        "correctionsOverlay": OVERLAY.name,
        "correctionsOverlaySha256": hashlib.sha256(OVERLAY.read_bytes()).hexdigest(),
        "correctionsApplied": applied,
        "repoCommit": git("rev-parse","HEAD"),
        "repoBranch": git("rev-parse","--abbrev-ref","HEAD"),
        "repoDirty": bool(git("status","--porcelain")),
        "atlasReadProvenance": [
          {"table":"Product Pricing","tableId":"tblqsjmkTrwSct7gv",
           "recordIds":[r for c in overlay["corrections"] for r in c["priceRecordIds"]],
           "readAt":"2026-10-06","readBy":"Airtable MCP search_records"}],
      },
      "productCount": len(products),
      "organisationCount": len(orgs),
      "validation": {"passed": ok, "checks": checks},
      "governedFields": GOVERNED,
      "products": products,
    }
    out["governedDigest"] = governed_digest(products)

    if a.mode == "production" and not ok:
        failed = [k for k,v in checks.items() if not v]
        raise SystemExit("PROMOTION REFUSED — validation failed: " + ", ".join(failed))

    dest = Path(a.out) if a.out else HERE / ("candidate-universe-%s.json" % a.mode)
    dest.write_text(json.dumps(out, indent=1))
    print("mode=%s  products=%d  orgs=%d  validation=%s  corrections=%s" %
          (a.mode, len(products), len(orgs), "PASS" if ok else "FAIL", ",".join(applied) or "none"))
    print("governedDigest=%s" % out["governedDigest"])
    print("written: %s" % dest.name)

if __name__ == "__main__": main()
