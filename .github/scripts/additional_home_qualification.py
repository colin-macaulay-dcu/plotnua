#!/usr/bin/env python3
"""PlotNua — additional-home-qualification-v1

INDEPENDENT BY CONSTRUCTION. This module does not import, read or reference
garden-room-qualification-v1, `Results Eligibility v1`, `Atlas Product
Certification Audit v1` (Gold) or any Garden Room tier. Those fields are
present in the snapshot and are deliberately ignored; a test asserts their
absence from this file rather than trusting the claim.

FIVE LAYERS, IN ORDER (Implementation Brief v1 §6.2):
  1 SOURCE MEMBERSHIP     Product Category == "Additional Home"
  2 HABITATION ADMISSION  Habitation Classification == CONFIRMED RESIDENTIAL HABITATION
  3 IRISH AVAILABILITY    evidence supports an Irish route
  4 PRODUCT EVIDENCE      enough to present truthfully
  5 PROPERTY FEASIBILITY  NOT EVALUATED HERE — Property Check's alone

THREE STATES:
  ELIGIBLE  recommendable to an Irish homeowner today
  HELD      genuinely an Additional Home; something is UNCONFIRMED
  EXCLUDED  positive evidence of a disqualifying fact

HELD is where UNKNOWN lives. UNKNOWN is never FALSE, and UNCONFIRMED is never
UNAVAILABLE. EXCLUDED requires evidence of a reason, never absence of evidence.
"""
from __future__ import annotations

import re

from atlas_common import cell, txt, classify_irish_availability

# BUMPED at the measurement evidence ruling (23 Sep 2026). One version string
# must not describe two different rules: the Class 3A upper-edge admission test
# changed materially, so the identifier changes with it. Membership,
# habitation admission, Irish availability and evidence sufficiency are all
# untouched — only the pathway filter moved.
RULE_VERSION = "additional-home-qualification-v1.1"
ADDITIONAL_HOME = "Additional Home"

CONFIRMED_HABITATION = "CONFIRMED RESIDENTIAL HABITATION"
HABITATION_STATES = [
    CONFIRMED_HABITATION,
    "PROBABLE — MORE EVIDENCE REQUIRED",
    "ANCILLARY / NON-DWELLING",
    "AMBIGUOUS",
    "CONTRADICTED",
    "UNKNOWN / NOT YET ASSESSED",
]
# Positive evidence that the product is not a dwelling. Everything else that is
# not CONFIRMED is HELD, never EXCLUDED.
HABITATION_EXCLUDES = {"ANCILLARY / NON-DWELLING", "CONTRADICTED"}

# ── Class 3A pathway constants (the pathway, NOT the category) ───────────────
BAND_MIN, BAND_MAX = 32.0, 45.0
# Founder ruling Q1, provisional. A PlotNua uncertainty guard, NOT a regulatory
# threshold and NOT part of Additional Home membership.
BAND_EDGE_TOLERANCE_M2 = 2.0

# ── THE MEASUREMENT EVIDENCE RULING (founder, 23 September 2026) ─────────────
# S.I. No. 340 of 2026 Class 3A condition 7 applies a maximum of 45 square
# metres to "the total area of such structures". The enacted wording does not
# expressly say whether that is supplier internal floor area or external
# building footprint, and the Information Note located through local-authority
# and building-control sources does not resolve it authoritatively. Historic
# Class 3 material using materially similar wording does not either.
#
# SO PLOTNUA DOES NOT MAKE THAT INFERENCE. This is an EVIDENCE rule, not an
# interpretation of planning law: a supplier's VERIFIED_INTERNAL figure is
# evidence of what the SUPPLIER measured, and is not by itself treated as
# establishing the measurement the statutory ceiling is expressed in.
#
# WHAT IT DOES NOT SAY. It does not say, assert or imply that any held product
# exceeds 45 m². Nothing here concludes non-compliance. The reason is missing
# measurement evidence, and the vocabulary below is written so that it cannot
# be read as anything else.
#
# UPPER BOUNDARY ONLY. The founder's ruling is explicit that the lower
# boundary must not inherit this logic until the evidence issue is shown to be
# equivalent there, and it is not: at 32 m² the internal/external difference
# moves a product AWAY from the floor, not across the ceiling, so an internal
# figure at or near 32 is the conservative reading rather than the risky one.
#
# Only a measurement of the whole structure can answer the ceiling question,
# so only VERIFIED_EXTERNAL admits at the upper edge. NOMINAL is a published
# designation rather than a verified measurement, and UNRESOLVED is already
# held by the Q1 guard below.
STATUTORY_AREA_BASES = frozenset({"VERIFIED_EXTERNAL"})

# ── area: a usable number and a verified measurement are different facts ────
AREA_FEATURES = ("internal floor area", "floor area")
AREA_DISOWNED = re.compile(
    r"(NO AREA PUBLISHED|No area or dimensions held|DO NOT RANK on any basis"
    r"|Numeral not treated as an area|REQUIRES PRODUCT-SPECIFIC VERIFICATION)", re.I)
BASIS_UNRESOLVED = re.compile(
    r"(MEASUREMENT BASIS\s*=\s*UNRESOLVED|BASIS UNCLEAR|BASIS UNKNOWN"
    r"|Internal versus external|not stated whether)", re.I)
BASIS_EXTERNAL = re.compile(r"(EXTERNAL (?:FOOTPRINT|AREA)|footprint area)", re.I)
BASIS_NOMINAL = re.compile(r"(VERIFIED NOMINAL SIZE|nominal plan area)", re.I)


def _area_evidence(feat_rows, feat_names):
    """(number, unit, basis, text). number is None when nothing usable is
    published — never 0. basis is one of VERIFIED_INTERNAL, VERIFIED_EXTERNAL,
    NOMINAL, UNRESOLVED."""
    best = (None, None, "UNRESOLVED", None)
    for r in feat_rows:
        fid = (r.get("fields", {}).get("Feature") or [None])[0]
        fname = (feat_names.get(fid) or "").lower()
        if fname not in AREA_FEATURES:
            continue
        body = txt(cell(r, "Value Text"))
        num = cell(r, "Value Number")
        unit = txt(cell(r, "Unit")) or "m²"
        if body and AREA_DISOWNED.search(body):
            # A record that refuses to state an area disowns any number held at
            # a broader scope. Carried across from the Garden Room integrity rule.
            return (None, None, "UNRESOLVED", body)
        if isinstance(num, (int, float)):
            if body and BASIS_UNRESOLVED.search(body):
                basis = "UNRESOLVED"
            elif body and BASIS_EXTERNAL.search(body):
                basis = "VERIFIED_EXTERNAL"
            elif body and BASIS_NOMINAL.search(body):
                basis = "NOMINAL"
            elif fname == "internal floor area":
                # The governed feature is named for what it measures.
                basis = "VERIFIED_INTERNAL"
            else:
                basis = "UNRESOLVED"
            return (float(num), unit, basis, body or None)
        if body and best[0] is None:
            best = (None, None, "UNRESOLVED", body)
    return best


# ── price: three states, and UNKNOWN is never converted into POA ────────────
QUOTE_TYPES = {"custom quote"}
NUMERIC_FIELDS = ("Base Price", "Price From", "Price To")


def _price_state(price_rows):
    """(state, amount, currency, priceType). Founder ruling Q2: a missing price
    alone neither holds nor excludes, and PRICE_NOT_PUBLISHED is never
    upgraded to POA by inference."""
    best = ("PRICE_NOT_PUBLISHED", None, None, None)
    for r in price_rows:
        ptype = txt(cell(r, "Price Type"))
        cur = txt(cell(r, "Currency")) or None
        amount = None
        for f in NUMERIC_FIELDS:
            v = cell(r, f)
            if isinstance(v, (int, float)) and v > 0:
                amount = float(v)
                break
        if amount is not None:
            return ("VERIFIED_NUMERIC_PRICE", amount, cur, ptype or None)
        if ptype.lower() in QUOTE_TYPES:
            best = ("EVIDENCED_POA_QUOTE", None, cur, ptype)
    return best


# ── Irish availability: four states, preserved ──────────────────────────────
EXPLICIT_UNCONFIRMED = re.compile(
    r"(REPUBLIC OF IRELAND UNCONFIRMED|AVAILABILITY UNKNOWN"
    r"|IRISH AVAILABILITY UNKNOWN|\bUNCONFIRMED\b)", re.I)


def _irish_state(feat_rows, feat_names):
    """(state, basis, scope, noPublishedRoute).

    Reuses the governed Garden Room vocabulary via atlas_common — the same
    Atlas field must not be read two ways. One distinction is added that the
    Garden Room tier does not need: an EXPLICIT 'unconfirmed' statement is
    reported as UNCONFIRMED, while silence is UNKNOWN. Neither is UNAVAILABLE.
    """
    ie_rows = [r for r in feat_rows
               if (feat_names.get((r.get("fields", {}).get("Feature") or [None])[0]) or
                   "").lower() == "irish availability"]
    state, basis, scope, _classified, no_route = classify_irish_availability(ie_rows)
    if state == "confirmed":
        return ("CONFIRMED", basis, scope, bool(no_route))
    if state == "unavailable":
        return ("UNAVAILABLE", basis, scope, bool(no_route))
    blob = " ".join(txt(cell(r, "Value Text")) for r in ie_rows)
    if EXPLICIT_UNCONFIRMED.search(blob):
        return ("UNCONFIRMED", basis, scope, bool(no_route))
    return ("UNKNOWN", basis, scope, bool(no_route))


# ── the rule ────────────────────────────────────────────────────────────────
def qualify(product, org_name, price_rows, feat_rows, feat_names, sources):
    held, excluded = [], []

    # LAYER 1 — source membership
    category = txt(cell(product, "Product Category"))
    membership = category == ADDITIONAL_HOME

    # LAYER 2 — habitation admission. Governed field only. No prose regex,
    # and category membership is never habitation proof.
    hab = txt(cell(product, "Habitation Classification")) or "UNKNOWN / NOT YET ASSESSED"
    habitation_ok = hab == CONFIRMED_HABITATION
    if not habitation_ok:
        if hab in HABITATION_EXCLUDES:
            excluded.append("habitation-not-a-dwelling")
        else:
            held.append("habitation-unconfirmed")

    # LAYER 3 — Irish availability, independent of habitation
    ie_state, ie_basis, ie_scope, no_route = _irish_state(feat_rows, feat_names)
    if ie_state == "UNAVAILABLE":
        excluded.append("irish-unavailable")
    elif ie_state != "CONFIRMED":
        held.append("irish-unconfirmed")

    # LAYER 4 — product evidence sufficiency. Q2: a missing price alone does
    # not hold. Identity and a traceable source do.
    name = txt(cell(product, "Product Name"))
    url = txt(cell(product, "Product URL"))
    has_source = bool(url) or bool(sources) or bool(txt(cell(product, "    Sources")))
    evidence_ok = bool(name) and bool(org_name) and has_source
    if not evidence_ok:
        held.append("evidence-insufficient")

    # LAYER 5 — property feasibility is NOT evaluated here. Property Check only.

    if excluded:
        state = "EXCLUDED"
    elif held:
        state = "HELD"
    else:
        state = "ELIGIBLE"

    price_state, amount, currency, ptype = _price_state(price_rows)
    area_n, area_u, area_basis, area_text = _area_evidence(feat_rows, feat_names)

    return {
        "state": state,
        "heldReasons": sorted(set(held)),
        "excludedReasons": sorted(set(excluded)),
        "layers": {"membership": membership, "habitation": habitation_ok,
                   "irishAvailability": ie_state == "CONFIRMED",
                   "productEvidence": evidence_ok},
        "habitationState": hab,
        "irish": {"state": ie_state, "basis": ie_basis, "scope": ie_scope,
                  "noPublishedRoute": no_route},
        "price": {"state": price_state, "amount": amount, "currency": currency,
                  "priceType": ptype},
        "area": {"number": area_n, "unit": area_u, "measurementBasis": area_basis,
                 "text": area_text},
    }


# ── Class 3A: a pathway filter OVER Additional Home, never its definition ───
def class_3a(q):
    """Membership of Additional Home is already settled before this runs. A
    product held or excluded here REMAINS an Additional Home."""
    if q["habitationState"] != CONFIRMED_HABITATION:
        return {"state": "NOT_A_CANDIDATE", "reason": "habitation-not-confirmed",
                "caveats": []}
    if q["state"] != "ELIGIBLE":
        return {"state": "NOT_A_CANDIDATE", "reason": "not-recommendation-eligible",
                "caveats": []}
    n = q["area"]["number"]
    if n is None:
        return {"state": "NOT_A_CANDIDATE", "reason": "no-usable-area", "caveats": []}
    if not (BAND_MIN <= n <= BAND_MAX):
        return {"state": "NOT_A_CANDIDATE", "reason": "outside-pathway-band",
                "caveats": []}
    basis = q["area"]["measurementBasis"]
    caveats = []
    if basis == "UNRESOLVED":
        near = (abs(n - BAND_MIN) <= BAND_EDGE_TOLERANCE_M2 or
                abs(n - BAND_MAX) <= BAND_EDGE_TOLERANCE_M2)
        if near:
            # Founder ruling Q1. Held from the PATHWAY only.
            return {"state": "HELD",
                    "reason": "area-basis-unresolved-at-band-edge",
                    "caveats": ["area-basis-unresolved"]}
        caveats.append("area-basis-unresolved")

    # THE UPPER-EDGE MEASUREMENT EVIDENCE RULE. Tested AFTER the Q1 guard, so
    # an unresolved basis keeps its own, older and more specific reason rather
    # than being relabelled by this one.
    #
    # Asymmetric BY EVIDENCE, not by preference: BAND_MAX only. See the note on
    # STATUTORY_AREA_BASES. `abs()` is deliberately not used — a product below
    # the ceiling by more than the tolerance is not at the edge, and one above
    # the ceiling never reaches here at all.
    if (BAND_MAX - n) <= BAND_EDGE_TOLERANCE_M2 and basis not in STATUTORY_AREA_BASES:
        # HELD FROM THE PATHWAY ONLY. The product remains an Additional Home,
        # remains CONFIRMED RESIDENTIAL HABITATION, remains ELIGIBLE, and keeps
        # its Irish availability and price evidence untouched.
        return {"state": "HELD",
                "reason": "statutory-area-not-established-at-upper-band-edge",
                "caveats": ["statutory-area-not-established"]}
    return {"state": "CANDIDATE", "reason": None, "caveats": caveats}
