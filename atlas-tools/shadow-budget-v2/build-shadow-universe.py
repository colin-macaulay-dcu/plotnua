#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SHADOW ONLY. Builds shadow-recommendation-universe-v2.json from the OPERATIVE
universe plus the governed price-basis axes file.

It never writes the operative artefact, never touches your-plot.html, never
reaches Airtable, and never carries curator prose into its output.

WHAT IT ADDS, per product, on top of the fields already present:

  priceRecordIds        list   truthful plural identity - see RECORD IDENTITY
  priceStatus           str    RENAMED from the misleading `priceBasis`
  priceType             str    whitespace-stripped select value
  priceScope            str
  vatStatus             str    Yes | No | Unknown | null -- NEVER inferred
  vatRate               num    published rate only; null otherwise
  priceBasisAxes        obj    {erection, siteWorks, delivery}
  priceBasisClass       str    DERIVED from the axes, never hand-typed
  priceBasisConfidence  str
  priceIsRangeFloor     bool
  priceSafeForMatching  bool
  priceEvidenceRef      obj    {axesFile, axesVersion, organisation, lastPriceCheck}

The legacy `priceBasis` key is REMOVED. It held Prices.Status under a name that
promised commercial basis; leaving both would guarantee a future misread.

RECORD IDENTITY. `priceRecordIds` is plural because adjudication is plural.
Rule 3 of adjudicate_price resolves a tie when "every candidate says the same
thing", so two records can jointly carry one verdict. The operative artefact
does not expose record ids at all, so this build emits [] and records
`priceRecordIdsAvailable: false` rather than inventing one. Nothing downstream
may treat [] as "no record" -- candidateCount already says how many exist.

Run: python3 atlas-tools/shadow-budget-v2/build-shadow-universe.py [--check]
"""
import json, pathlib, sys, unicodedata, datetime

ROOT = pathlib.Path(__file__).resolve().parents[2]
HERE = pathlib.Path(__file__).resolve().parent
SRC  = ROOT / "garden-room-recommendation-universe-v1.json"
AXES = HERE / "price-basis-axes-v1.json"
OUT  = HERE / "shadow-recommendation-universe-v2.json"
CHECK = "--check" in sys.argv

def die(msg):
    print("REFUSED: " + msg); sys.exit(1)

def fold(s):
    """Diacritic-insensitive key so 'Sommarnojen' matches 'Sommarnojen'."""
    if not s: return ""
    return "".join(c for c in unicodedata.normalize("NFKD", s)
                   if not unicodedata.combining(c)).strip().lower()

# G1 . inputs must be the ones this script was written against
if not SRC.exists(): die("the operative universe is not where it was: %s" % SRC)
if not AXES.exists(): die("the price-basis axes file is missing: %s" % AXES)
src  = json.loads(SRC.read_text(encoding="utf-8"))
axes = json.loads(AXES.read_text(encoding="utf-8"))
if src.get("schema") != "plotnua.garden-room-recommendation-universe":
    die("the source artefact is not the Garden Room universe (schema=%r)" % src.get("schema"))
if not src.get("products"): die("the source artefact carries no products")

ORG = {fold(k): v for k, v in axes["byOrganisation"].items()}
PRD = {fold(k): v for k, v in axes["byProduct"].items()}

# G2 . the derivation is a pure function of the three axes. Order matters and is
#      asserted below: an EXCLUDED delivery only means ex-works when erection is
#      also excluded, otherwise an installed room with paid delivery would be
#      misread as a collection-only product.
def derive(ax):
    e, s, d = ax["erection"], ax["siteWorks"], ax["delivery"]
    if e == "EXCLUDED" and d == "EXCLUDED":        return "EX_WORKS"
    if e == "INCLUDED" and s == "INCLUDED":        return "ERECTED_WITH_SERVICES"
    if e == "INCLUDED" and s == "EXCLUDED":        return "ERECTED_SERVICES_EXCLUDED"
    if e == "INCLUDED" and s == "UNKNOWN":         return "ERECTED_SERVICES_UNKNOWN"
    if e == "EXCLUDED" and d == "INCLUDED":        return "DELIVERED_SHELL"
    if e == "EXCLUDED":                            return "KIT_SELF_ASSEMBLY"
    return "UNKNOWN"                               # fails closed

VOCAB = {"KIT_SELF_ASSEMBLY","DELIVERED_SHELL","ERECTED_SERVICES_EXCLUDED",
         "ERECTED_SERVICES_UNKNOWN","ERECTED_WITH_SERVICES","EX_WORKS","UNKNOWN"}
UNSAFE_CONF = {"UNSAFE", "CONFLICTED"}
AX_UNKNOWN = {"erection":"UNKNOWN","siteWorks":"UNKNOWN","delivery":"UNKNOWN",
              "confidence":"NO_EVIDENCE_RECORDED","quote":None}

# G3 . no curator prose may reach the output. The axes file carries a `quote`
#      for human audit; it is read here and deliberately NOT emitted.
FORBIDDEN_KEYS = ("quote", "basisNotes", "knownExclusions", "ingestionNotes")

out, stats = [], {}
def bump(k): stats[k] = stats.get(k, 0) + 1

for p in src["products"]:
    pe = p.get("priceEvidence") or {}
    price = p.get("price")
    priced = isinstance(price, (int, float)) and price > 0

    ev = PRD.get(fold(p.get("name"))) or ORG.get(fold(p.get("organisation"))) or AX_UNKNOWN
    ax = {"erection": ev["erection"], "siteWorks": ev["siteWorks"], "delivery": ev["delivery"]}
    cls = derive(ax)
    if cls not in VOCAB: die("derive() produced %r, which is outside the closed vocabulary" % cls)
    # Confidence is a property of the PRICE, not of the supplier's build model.
    # The axes are legitimately supplier-level (how a maker sells is a maker
    # fact), but "this figure is unsafe" belongs to the figure. An unpriced
    # product therefore carries NO_PRICE, so the UNSAFE count means what it says.
    conf = ev["confidence"] if priced else "NO_PRICE"

    ptype = (pe.get("priceType") or "").strip() or None
    # A range floor is a Price From used as the price, OR a published
    # Starting From, OR a record whose own evidence says the figure is a
    # tier/width floor. All three are governed facts, none is a guess.
    range_floor = bool(
        (pe.get("base") in (None, "") and pe.get("from") not in (None, ""))
        or ptype == "Starting From"
        or (ev is not AX_UNKNOWN and conf == "PARTIAL" and p.get("organisation") == "Sprout Pod")
    )
    safe = priced and conf not in UNSAFE_CONF

    q = dict(p)
    q.pop("priceBasis", None)                       # the misleading name goes
    q.update({
        "priceRecordIds": [],
        "priceRecordIdsAvailable": False,
        "priceStatus": pe.get("status"),
        "priceType": ptype,
        "priceScope": pe.get("evidenceScope"),
        "vatStatus": pe.get("includesVat"),
        "vatRate": None,                            # never inferred; no source field exists
        "priceBasisAxes": ax,
        "priceBasisClass": cls,
        "priceBasisConfidence": conf,
        "priceIsRangeFloor": range_floor,
        "priceSafeForMatching": safe,
        "priceEvidenceRef": {
            "axesFile": AXES.name, "axesVersion": axes["version"],
            "organisation": p.get("organisation"),
            "lastPriceCheck": None,
        },
    })
    for k in FORBIDDEN_KEYS:
        if k in q: die("forbidden key %r reached the shadow payload" % k)
    out.append(q)
    bump("class:" + cls); bump("conf:" + str(conf))
    if priced: bump("priced")
    if range_floor: bump("rangeFloor")
    if priced and not safe: bump("pricedButUnsafe")

# G4 . post-conditions. A build that silently classified nothing is a bug.
if len(out) != len(src["products"]): die("product count changed during the build")
if stats.get("class:UNKNOWN", 0) == len(out): die("every product derived UNKNOWN; the axes file is not being read")
if stats.get("class:ERECTED_WITH_SERVICES", 0) == 0: die("no product reached ERECTED_WITH_SERVICES; derive() is not exercising its axes")
if stats.get("pricedButUnsafe", 0) == 0: die("no priced product was marked unsafe; priceSafeForMatching is inert")

payload = {
    "schema": "plotnua.garden-room-recommendation-universe.shadow",
    "version": "2.0.0-shadow",
    "shadow": True,
    "generated": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
    "builtFrom": {"file": SRC.name, "generated": src.get("generated"),
                  "version": src.get("version"), "dryRun": src.get("dryRun")},
    "basisAxesFile": AXES.name, "basisAxesVersion": axes["version"],
    "notAuthorisedForRuntime": "SHADOW. Not loaded by your-plot.html. Not a replacement for the operative universe.",
    "newEvidenceDeliberatelyExcluded": [
        "Garden Rooms (gardenrooms.ie) published prices",
        "Shomera revised six-model prices",
        "Ecohouse Building Systems published prices",
        "the Big Man Tiny Homes EUR60,000 withdrawal",
    ],
    "newEvidenceNote": "Phase 4 section 6: research findings are NOT baked into code. They are proposed for founder review in PROPOSED-ATLAS-UPDATES.md and reach no artefact until authorised.",
    "stats": stats,
    "products": out,
}
if CHECK:
    print("CHECK ONLY - nothing written"); print(json.dumps(stats, indent=1, sort_keys=True)); sys.exit(0)
OUT.write_text(json.dumps(payload, indent=1, ensure_ascii=False), encoding="utf-8")
print("wrote %s  (%d products)" % (OUT.name, len(out)))
for k in sorted(stats): print("   %-38s %d" % (k, stats[k]))
