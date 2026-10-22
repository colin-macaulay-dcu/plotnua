#!/usr/bin/env python3
"""PlotNua — generate_wellness_universe.py

Builds wellness-universe-v1.json — the published eligibility file for Atlas
Product Category "Wellness / Sauna" (DISC-001 Garden Retreat: saunas, hot tubs,
cold plunges) — from a frozen Atlas snapshot.

THE THIRD UNIVERSE, BUILT THE SAME WAY AS THE SECOND. Founder decision, 14 Oct
2026 ("OGNYX public integration — PROCEED"): reuse PlotNua's existing
publication architecture, no supplier-specific system. So this is the
Additional Home pattern, narrowed:

  * reads a snapshot only; no Airtable client, cannot write production;
  * the PUBLICATION GATE is the Additional Home generator's own
    publication_hold(), imported rather than copied, so there is one rule;
    every record carries publicVisibility and the artefact declares the gate,
    so readers fail closed;
  * qualification is EVIDENCE ONLY and never re-decides permission:
      EXCLUDED  no organisation, no product URL, or no source;
      HELD      Atlas records a contradiction or evidence gap (Standards
                carries BLOCKED) -- the supplier's own page disagrees with
                itself, so PlotNua shows neither figure -- or no single
                verified EUR price is recorded;
      ELIGIBLE  otherwise.
    A product is PUBLIC only if it is ELIGIBLE and its organisation derives
    PUBLISHABLE. Nothing is published "automatically": a new wellness
    supplier with no rights record holds (publication-record-missing).

REVISION 2, 14 Oct 2026 (Garden Retreat restructure brief: "populate the
full wellness maker universe ... use the established gate ... no
legacy-baseline additions"):
  * The gate is the Additional Home rule MINUS its legacy baseline. That
    baseline grandfathers organisations published on Additional Home before
    14 Oct 2026; it never covered wellness, so a wellness organisation with
    no rights record holds (publication-record-missing) even if the baseline
    names it (MyCabin.ie and Hansa24 Group are both named there).
  * Availability is no longer required: Irish availability is UNCONFIRMED
    for every record and is never emitted as a claim, so its absence cannot
    make a record less true. A verified EUR price IS required.
  * Price: Base Price, or Price From when Base Price is absent (Tanktribe
    records its 'from' prices there). The basis names the price type, the
    evidence scope when it is range-level, and the VAT position.
  * kinds: closed tokens sauna / hot-tub / cold-plunge / combination, from
    the Atlas Product Type, else from the product's own name; a product
    that is genuinely more than one (Tanktribe WILD TUB, recorded in Atlas
    as dual-use) carries both. Unclassifiable records hold.

REVISION 3, 14 Oct 2026 (founder decision "Garden Retreat — controlled
text-only publication expansion"): a SECOND, NARROWER listing basis.
  * A product is public when ELIGIBLE and either (a) its organisation's own
    rights record derives PUBLISHABLE (listingBasis SUPPLIER_PERMISSION), or
    (b) its organisation has NO rights record and is listed in
    atlas-tools/public-information-listings.json (listingBasis
    PUBLIC_INFORMATION). A rights record always wins: a decline, a hold or a
    review request in a record is never overridden by the register.
  * PUBLIC_INFORMATION is not permission. It grants no image (the maker
    explorer draws images only from rights records), records no consent and
    adds one product-level condition: the product's own page must be VERIFIED
    in atlas-tools/maker-product-links-v1.json (HTTPS, the maker's own domain,
    HTTP 200, same-host same-path redirects only, the page names the product).
    A product that fails it holds (product-page-not-verified).
  * A product Atlas records as a sauna-and-hot-tub combination building
    carries the kinds combination, sauna AND hot-tub: one record, shown under
    both tabs, never duplicated.

REVISION 4, 22 Oct 2026 (founder review "TimberIN final coordinated release —
final correction"): SUPPLIER-PUBLISHED CURRENCY. A verified price is still
recorded in EUR in Atlas; the one exception is a record listed in
atlas-tools/price-currency-corrections.json, whose supplier publishes the
SAME amount in another currency (TimberIN: GBP). Such a price keeps its Atlas
amount, type and VAT basis exactly and carries the supplier's currency; it is
never converted. The register applies only while the Atlas amount equals the
evidenced amount: if Atlas moves, generation refuses until it is reviewed.

PUBLIC-DISCLOSURE FIREWALL. Description, Notes, Standards prose and Habitation
basis are read and NEVER exported. What reaches the artefact is identity,
the Atlas product type, a verified 'from' price with its basis, and closed
state tokens. No health, VAT, delivery, installation or lead-time statement is
ever emitted; a price whose VAT position is unknown says so in its basis.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from atlas_common import cell, links, txt, fail          # noqa: E402
import generate_additional_home_universe as AH              # noqa: E402
from generate_additional_home_universe import NO_RECORD_HOLD  # noqa: E402

SCHEMA = "plotnua.wellness-universe"
VERSION = "1.2.0"
RULE_VERSION = "wellness-qualification-v3"
CATEGORY = "Wellness / Sauna"
PRICE_LEAD = {"Starting From": "Published 'from' price",
              "Standard Price": "Published price",
              "Sale Price": "Published sale price"}
VAT_TAIL = {"Unknown": ". The supplier does not state whether it includes VAT.",
            "Yes": ", including VAT.",
            "No": ", excluding VAT."}
KINDS = ("sauna", "hot-tub", "cold-plunge", "combination")
# Atlas records WILD TUB as dual-use: "wood-fired hot tub when the heating
# coil is lit and natural cold plunge when it is not" (Product description).
KIND_OVERRIDES = {"recdsCR4RW4h9D9TO": ["hot-tub", "cold-plunge"]}
# The closed set of fields a public record may carry.
PUBLIC_FIELDS = {"id", "productCode", "productName", "organisation",
                 "productCategory", "productType", "kinds", "productUrl", "price", "irish",
                 "qualification", "publicVisibility", "holdReason", "listingBasis"}
REPO = Path(__file__).resolve().parent.parent.parent
REGISTER = REPO / "atlas-tools" / "public-information-listings.json"
LINKS = REPO / "atlas-tools" / "maker-product-links-v1.json"
SUPPLIER_PERMISSION, PUBLIC_INFORMATION = "SUPPLIER_PERMISSION", "PUBLIC_INFORMATION"
PAGE_NOT_VERIFIED = "product-page-not-verified"


CURRENCY_REGISTER = REPO / "atlas-tools" / "price-currency-corrections.json"
CURRENCY_LEAD = {"GBP": ", in pounds sterling as the supplier publishes it"}


def currency_corrections():
    """id -> correction, from the founder-approved register (empty if absent)."""
    if not CURRENCY_REGISTER.exists():
        return {}
    reg = json.loads(CURRENCY_REGISTER.read_text(encoding="utf-8"))
    out = {}
    for c in reg.get("corrections", []):
        if c.get("publishedCurrency") not in CURRENCY_LEAD or c.get("atlasCurrency") != "EUR":
            fail("price-currency-corrections: unsupported correction for %s" % c.get("id"))
        out[c["id"]] = c
    return out


def corrected_price(pid, price, corr=None):
    """The supplier's published currency for a register-listed record.
    Amount, type and VAT position are kept exactly; nothing is converted."""
    c = (corr if corr is not None else currency_corrections()).get(pid)
    if not c or price.get("state") != "VERIFIED_NUMERIC_PRICE":
        return price
    if price.get("amount") != c["amount"] or price.get("type") != c["priceType"]:
        fail("price-currency-corrections: %s Atlas price %r %s no longer matches the evidenced %r %s; "
             "review the register" % (pid, price.get("amount"), price.get("type"), c["amount"], c["priceType"]))
    if price.get("currency") == c["publishedCurrency"]:
        return price
    if price.get("currency") != c["atlasCurrency"]:
        fail("price-currency-corrections: %s carries %r" % (pid, price.get("currency")))
    lead, tail = PRICE_LEAD[price["type"]], price["basis"][len(PRICE_LEAD[price["type"]]):]
    return dict(price, currency=c["publishedCurrency"],
                basis=lead + CURRENCY_LEAD[c["publishedCurrency"]] + tail)


def price_of(rows, pid=None, corr=None):
    """VERIFIED_NUMERIC_PRICE only from exactly one verified EUR row (or, for a
    record in the currency register, the same row under the supplier's own
    published currency)."""
    live = [r for r in rows if txt(cell(r, "Status")) == "Verified"]
    if len(live) != 1:
        return {"state": "PRICE_NOT_ESTABLISHED"}
    r = live[0]
    amt = cell(r, "Base Price")
    if amt in (None, ""):
        amt = cell(r, "Price From")
    corr = corr if corr is not None else currency_corrections()
    cur = txt(cell(r, "Currency"))
    allowed = {"EUR"} | ({corr[pid]["publishedCurrency"]} if pid in corr else set())
    if not isinstance(amt, (int, float)) or amt <= 0 or cur not in allowed:
        return {"state": "PRICE_NOT_ESTABLISHED"}
    ptype = txt(cell(r, "Price Type"))
    if ptype not in PRICE_LEAD:
        return {"state": "PRICE_NOT_ESTABLISHED"}
    vat = txt(cell(r, "Price Includes VAT")) or "Unknown"
    lead = PRICE_LEAD[ptype]
    if txt(cell(r, "Evidence Scope")) == "Range-Level":
        lead += " for the range, read from the supplier's range page"
    price = {"state": "VERIFIED_NUMERIC_PRICE", "amount": amt, "currency": "EUR",
             "type": ptype, "basis": lead + VAT_TAIL.get(vat, VAT_TAIL["Unknown"])}
    if pid in corr:
        if cur == corr[pid]["publishedCurrency"]:
            price["currency"] = corr[pid]["atlasCurrency"]  # normalise, then correct once
        return corrected_price(pid, price, corr)
    return price


def kinds_of(p):
    """Closed kind tokens; [] when the record cannot be classified."""
    if p["id"] in KIND_OVERRIDES:
        return list(KIND_OVERRIDES[p["id"]])
    for s in (txt(cell(p, "Product Type")), txt(cell(p, "Product Name"))):
        low = s.lower()
        if not low:
            continue
        if "sauna" in low and "hot tub" in low:
            # One building that is both: listed under both, never duplicated.
            return ["combination", "sauna", "hot-tub"]
        if "cold plunge" in low or "ice bath" in low:
            return ["cold-plunge"]
        if "hot tub" in low:
            return ["hot-tub"]
        if "sauna" in low:
            return ["sauna"]
    return []


_WGATE = None


_REGISTER = None


def public_information_register():
    """{normalised name: row} for rows that meet the register's own rules.
    A row that claims permission, imagery or an objection is refused, not
    skipped: the register cannot be used to smuggle consent in."""
    global _REGISTER
    if _REGISTER is None:
        doc = json.loads(REGISTER.read_text(encoding="utf-8"))
        if (doc.get("decision") or {}).get("scope") != CATEGORY:
            fail("the public-information register is not scoped to %r" % CATEGORY)
        out = {}
        for row in doc.get("organisations") or []:
            if (row.get("basis") != PUBLIC_INFORMATION or row.get("supplier_permission") is not False
                    or row.get("imagery") != "none" or row.get("objection") != "none recorded"
                    or not row.get("objection_check") or not row.get("maker_identity")):
                fail("public-information register row for %r is malformed" % row.get("name"))
            out[AH._norm_org(row["name"])] = row
        for row in doc.get("not_listed") or []:
            if AH._norm_org(row["name"]) in out:
                fail("%r is both listed and not listed" % row["name"])
        _REGISTER = out
    return _REGISTER


def wellness_hold(org_name):
    """(hold reason or None, listing basis or None).

    The Additional Home gate WITHOUT its legacy baseline decides first: an
    organisation with a rights record is decided by that record, whatever it
    says. Only an organisation with NO rights record may be listed on the
    public-information basis, and only if the register names it."""
    global _WGATE
    if _WGATE is None:
        _WGATE = AH._gate_index()
    key = AH._norm_org(org_name)
    if key and key in _WGATE:
        hold = _WGATE[key]
        return hold, (None if hold else SUPPLIER_PERMISSION)
    if key and key in public_information_register():
        return None, PUBLIC_INFORMATION
    return NO_RECORD_HOLD, None


_LINKS = None


def page_verified(pid, url):
    global _LINKS
    if _LINKS is None:
        _LINKS = json.loads(LINKS.read_text(encoding="utf-8"))["links"] if LINKS.exists() else {}
    e = _LINKS.get(pid)
    return bool(e and e.get("state") == "VERIFIED" and url and e.get("url") == url)


def qualify(p, org, price, kinds):
    excluded, held = [], []
    if not org:
        excluded.append("no-organisation")
    if not txt(cell(p, "Product URL")):
        excluded.append("no-product-url")
    if not links(p, "Sources"):
        excluded.append("no-source")
    if price["state"] != "VERIFIED_NUMERIC_PRICE":
        held.append("evidence-incomplete")
    if not kinds:
        held.append("kind-unclassified")
    if "BLOCKED" in txt(cell(p, "Standards")).upper():
        held.append("recorded-contradiction")
    state = "EXCLUDED" if excluded else ("HELD" if held else "ELIGIBLE")
    return {"rule": RULE_VERSION, "state": state,
            "heldReasons": held, "excludedReasons": excluded}


SORT_KEY = lambda r: (r["organisation"] or "", r["productName"].lower())


def summarise(emitted, snapshot_sha, snapshot_scope, source_count):
    """Every header field the universe derives from its records, in the order
    the artefact has always carried them. Shared with the targeted publisher
    (atlas-tools/publish-targeted-update.py), which re-derives the header of a
    spliced product list with THIS function rather than its own copy."""
    public = [r for r in emitted if r["qualification"]["state"] == "ELIGIBLE"
              and r["publicVisibility"] == "PUBLISHABLE"]
    count = lambda s: sum(1 for r in emitted if r["qualification"]["state"] == s)
    return {
        "publicationGate": {
            "version": "supplier-publication-gate-v1",
            "rule": ("public visibility is derived from permission state, "
                     "listing-review state and asset approval by the Additional "
                     "Home generator's gate index, without its legacy baseline. "
                     "An organisation with no rights record holds unless the "
                     "founder's public-information register (14 Oct 2026) lists it, "
                     "in which case each product also needs a VERIFIED product page; "
                     "that basis is factual text only, never permission or imagery. "
                     "A product is public only when ELIGIBLE and PUBLISHABLE."),
            "publicInformationRegister": "atlas-tools/public-information-listings.json",
            "publicInformationOrganisations": sorted({r["organisation"] for r in emitted
                                                     if r["listingBasis"] == PUBLIC_INFORMATION}),
            "heldOrganisations": sorted({r["organisation"] for r in emitted
                                         if r["publicVisibility"] == "HOLD" and r["organisation"]}),
        },
        "snapshotSha256": snapshot_sha,
        "snapshotScope": snapshot_scope,
        "sourceCategory": CATEGORY,
        "sourceCategoryCount": source_count,
        # eligibleCount counts what a homeowner may see: ELIGIBLE AND PUBLISHABLE.
        "eligibleCount": len(public),
        "organisationCount": len({r["organisation"] for r in public}),
        # Public products per kind (a dual-use product counts under each kind
        # it carries), so a page that shows one kind can be held to a header.
        "kindCounts": {k: sum(1 for r in public if k in r["kinds"]) for k in KINDS},
        "kindOrganisationCounts": {k: len({r["organisation"] for r in public if k in r["kinds"]})
                                   for k in KINDS},
        "heldCount": count("HELD"),
        "excludedCount": count("EXCLUDED"),
        "gateHeldCount": sum(1 for r in emitted if r["qualification"]["state"] == "ELIGIBLE"
                             and r["publicVisibility"] != "PUBLISHABLE"),
        "listingBasisCounts": {b: sum(1 for r in public if r["listingBasis"] == b)
                               for b in (SUPPLIER_PERMISSION, PUBLIC_INFORMATION)},
        "products": emitted,
    }


def main():
    ap = argparse.ArgumentParser(description="Wellness / Sauna universe (snapshot only).")
    ap.add_argument("--snapshot", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    raw_bytes = Path(args.snapshot).read_bytes()
    raw = json.loads(raw_bytes)
    orgs = {r["id"]: txt(cell(r, "Organisation Name")) for r in raw["organisations"]}
    by_prod = lambda rows: {pid: [r for r in rows if pid in links(r, "Product")]
                            for pid in {x for r in rows for x in links(r, "Product")}}
    pricing = by_prod(raw.get("pricing", []))

    corr = currency_corrections()
    src = [p for p in raw["products"] if txt(cell(p, "Product Category")) == CATEGORY]
    if not src:
        fail("No product carries Product Category %r; refusing to write an empty universe." % CATEGORY)

    emitted = []
    for p in src:
        oid = (links(p, "Organisation") or [None])[0]
        org = orgs.get(oid) if oid else None
        price = price_of(pricing.get(p["id"], []), p["id"], corr)
        kinds = kinds_of(p)
        q = qualify(p, org, price, kinds)
        hold, basis = wellness_hold(org) if org else (NO_RECORD_HOLD, None)
        # The page condition is a PUBLICATION condition for an otherwise
        # eligible product; a product already held on evidence keeps that
        # reason rather than gaining a second one.
        if (basis == PUBLIC_INFORMATION and q["state"] == "ELIGIBLE"
                and not page_verified(p["id"], txt(cell(p, "Product URL")))):
            hold, basis = PAGE_NOT_VERIFIED, None
        rec = {
            "id": p["id"],
            "productCode": txt(cell(p, "Product Code")) or None,
            "productName": txt(cell(p, "Product Name")),
            "organisation": org,
            "productCategory": CATEGORY,
            "productType": txt(cell(p, "Product Type")) or None,
            "kinds": kinds,
            # The maker's own product page (Atlas Product URL), emitted only
            # for a record that is public; whether it may be LINKED is decided
            # by the maker explorer against the rights record (link-back).
            "productUrl": None,
            "price": price,
            # Irish availability is a per-product Atlas feature value. None is
            # recorded for these products, so it is UNCONFIRMED -- never
            # inferred from where a company is registered.
            "irish": {"state": "UNCONFIRMED"},
            "qualification": q,
            "publicVisibility": "HOLD" if hold else "PUBLISHABLE",
            "holdReason": hold,
            # Why a public record may be shown: the maker's own rights record,
            # or PlotNua's factual research on the public-information basis.
            # Never both, never a permission when it is the second.
            "listingBasis": basis if (not hold and q["state"] == "ELIGIBLE") else None,
        }
        if set(rec) != PUBLIC_FIELDS:
            fail("a record carries a field outside the public set")
        emitted.append(rec)

    url_of = {p["id"]: txt(cell(p, "Product URL")) or None for p in src}
    for r in emitted:
        if r["qualification"]["state"] == "ELIGIBLE" and r["publicVisibility"] == "PUBLISHABLE":
            u = url_of.get(r["id"])
            r["productUrl"] = u if u and u.startswith("https://") else None
    emitted.sort(key=SORT_KEY)
    payload = dict({"schema": SCHEMA, "version": VERSION,
                    "generated": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "qualificationRuleVersion": RULE_VERSION},
                   **summarise(emitted, hashlib.sha256(raw_bytes).hexdigest(),
                               raw.get("source", ""), len(src)))
    out = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    for bad in ("health", "therapeutic", "vat included", "including vat",
                "free delivery", "installation included", "lead time"):
        if bad in json.dumps([{k: v for k, v in r.items() if k != "price"} for r in emitted]).lower():
            fail("the firewall leaked %r into a public record" % bad)
    Path(args.out).write_text(out, encoding="utf-8")
    print("WELLNESS universe: %d source, %d public (ELIGIBLE and PUBLISHABLE), "
          "%d held on evidence, %d excluded, %d held by the gate"
          % (len(src), payload["eligibleCount"], payload["heldCount"],
             payload["excludedCount"], payload["gateHeldCount"]))


if __name__ == "__main__":
    main()
