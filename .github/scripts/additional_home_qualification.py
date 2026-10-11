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
# ── CLASS 3A IS TIME-LIMITED, AND THAT IS NOT A PRODUCT FACT ────────────────
# S.I. No. 340 of 2026 inserted Class 3A with effect from 27 JULY 2026. Its
# condition 1 sets a relevant period ending 31 DECEMBER 2030, and condition 2
# admits only development COMMENCED AND COMPLETED inside that period.
#
# DELIBERATELY NOT ENCODED BELOW. No current date is read anywhere in this
# module. A product does not stop being an Additional Home, or stop being the
# right building for someone, because a statutory route closes — and a rule
# that silently changed its own output as the clock moved would be untestable.
# The sunset belongs to the ROUTE: it is carried in governance documentation
# and surfaced to the homeowner in the Property Check, not applied to products.
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
#
# NAMED FOR WHAT IT IS (27 Sep 2026). This set was called STATUTORY_AREA_BASES
# and its hold reason "statutory-area-not-established". Those names implied the
# statute names a measurement basis. IT DOES NOT: S.I. No. 340 of 2026 Class 3A
# condition 7 says only "the total area of such structures", unqualified. The
# comment block above always said so; the identifiers contradicted it. Verified
# external is PLOTNUA'S CONSERVATIVE EVIDENCE PROXY for a question the statute
# leaves open, and the names now say that. Behaviour is unchanged.
ACCEPTED_CEILING_AREA_BASES = frozenset({"VERIFIED_EXTERNAL"})

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


# VAT BASIS. Required wherever an amount exists, and it has no safe default.
# BIOBUILDS is the argument for this field: Atlas carried "+VAT" in prose
# where no field could see it, and the prose was wrong by the time anyone
# looked. VAT_UNKNOWN is a real state and must never be rendered as though it
# meant VAT-inclusive.
# MEASURED AGAINST THE REAL BASE, 11 October 2026, NOT DESIGNED IN THE
# ABSTRACT. My Phase 1 design proposed creating a new "Price Basis" field.
# Reading Airtable read-only showed that was wrong twice over: a field called
# "Price Includes VAT" ALREADY EXISTS on Pricing and is already populated, and
# my first implementation read the invented name, so it returned VAT_UNKNOWN
# for all 36 priced Additional Home products including the 20 that say "Yes".
# Inventing a parallel field would have duplicated live data and thrown away
# evidence somebody had already gathered.
#
# The four observed option values, counted across the 44 real pricing rows
# attached to the 46 Additional Home products.
VAT_BASIS = {
    "yes":           "INCLUDES_VAT",
    "no":            "EXCLUDES_VAT",
    "excluding vat": "EXCLUDES_VAT",
    "unknown":       "VAT_UNKNOWN",
}


def _amount_of(row):
    """The first positive number across the three numeric price fields."""
    for f in NUMERIC_FIELDS:
        v = cell(row, f)
        if isinstance(v, (int, float)) and v > 0:
            return float(v)
    return None


def _configuration_of(row):
    """The named configuration this pricing row prices, or None.

    A row without the field behaves exactly as it did before this change,
    which is what keeps every other supplier in the universe untouched."""
    return txt(cell(row, "Configuration")) or None


def _vat_basis_of(row):
    """The EXISTING governed field, not a new one. An unrecognised or absent
    value is VAT_UNKNOWN, never a silent assumption of inclusive."""
    raw = txt(cell(row, "Price Includes VAT")).strip().lower()
    return VAT_BASIS.get(raw, "VAT_UNKNOWN")


# ── WHAT A PRICE INCLUDES, AS TOKENS RATHER THAN PROSE ─────────────────────
#
# The governed evidence is a curator's paragraph in Known Exclusions: sources,
# supersession notes, items deliberately not claimed. The Garden Room price
# contract already refuses to let that field reach the runtime, and it is
# right to -- publishing it would publish PlotNua's working out.
#
# These anchors recognise a CLOSED set of commercial terms in it. Each token
# has one approved homeowner sentence, held in the reader. Recognition is the
# only inference permitted here, and it fails in the honest direction:
# wording the anchors do not match produces NO token, so the term is not
# stated. No token ever means "included" -- absence of evidence is not
# absence of a cost, and no reader may say otherwise.
COMMERCIAL_TERM_ANCHORS = (
    # (token, required substrings -- ALL must appear, case-insensitively)
    ("TRANSPORT_AND_ASSEMBLY_INCLUDED",
     ("transport", "assembly", "ground screws", "are included")),
    ("FOUNDATIONS_UTILITIES_SITEWORKS_QUOTED_SEPARATELY",
     ("foundations", "utility connections", "site works", "quoted per project")),
    ("KITCHEN_FURNITURE_AND_APPLIANCES_EXCLUDED",
     ("kitchen furniture", "appliances", "not included")),
    ("DELIVERY_INSTALLATION_FOUNDATION_EXCLUDED",
     ("delivery, installation and foundation", "not included")),
)


def _commercial_terms_of(row):
    """The recognised terms on ONE pricing row, in anchor order.

    Anchor order, not evidence order, so the same facts always present in the
    same sequence and a reader cannot be made to reorder by a curator's
    sentence being rewritten."""
    blob = txt(cell(row, "Known Exclusions")).lower()
    if not blob:
        return []
    return [tok for tok, needles in COMMERCIAL_TERM_ANCHORS
            if all(n in blob for n in needles)]


def _vat_rate_of(row):
    v = cell(row, "VAT Rate %")
    return float(v) if isinstance(v, (int, float)) else None


def _price_state(price_rows):
    """(state, amount, currency, priceType, extra).

    Founder ruling Q2 is unchanged: a missing price alone neither holds nor
    excludes, and PRICE_NOT_PUBLISHED is never upgraded to POA by inference.

    WHAT CHANGED, AND WHY IT HAD TO. This function used to RETURN on the first
    row carrying a number. A supplier who publishes two prices -- BIOBUILDS
    publishes Exterior Finished and Turnkey for each model -- would therefore
    have had one of them chosen by Airtable's row order and the other silently
    discarded, with no flag, no caveat and no count. The output would have
    looked exactly as verified as a single-price product. That is the failure
    this rewrite exists to make impossible.

    Two numeric rows now produce one of two outcomes and never a quiet guess:

      * they carry Configuration -> both are kept, ordered cheapest first
      * they do not               -> PRICE_AMBIGUOUS_MULTI_ROW, a HELD state
                                     that says what is true: more than one
                                     price is published and Atlas cannot say
                                     which one to show.
    """
    best = ("PRICE_NOT_PUBLISHED", None, None, None, {})
    numeric = [r for r in price_rows if _amount_of(r) is not None]

    if len(numeric) > 1 and not all(_configuration_of(r) for r in numeric):
        # Refuse rather than pick. An arbitrary figure that looks verified is
        # worse than an honest hold.
        return ("PRICE_AMBIGUOUS_MULTI_ROW", None, None, None,
                {"ambiguousRowCount": len(numeric)})

    if numeric:
        configs = []
        for r in numeric:
            key = _configuration_of(r)
            configs.append({
                "key": (key or "").strip().lower().replace(" ", "-") or None,
                "label": key,
                "amount": _amount_of(r),
                "priceType": txt(cell(r, "Price Type")) or None,
                # A term recognised on the Turnkey row is true of Turnkey, and
                # of nothing else until its own row says so.
                "terms": _commercial_terms_of(r),
            })
        # Cheapest first, and the order is part of the contract so a renderer
        # can take [0] without re-deriving anything.
        configs.sort(key=lambda c: c["amount"])

        first = numeric[0]
        bases = {_vat_basis_of(r) for r in numeric}
        # Rows disagreeing about VAT is not something to average away.
        basis = bases.pop() if len(bases) == 1 else "VAT_UNKNOWN"
        rates = {_vat_rate_of(r) for r in numeric if _vat_rate_of(r) is not None}
        rate = rates.pop() if len(rates) == 1 else None

        # THE INTERSECTION, NEVER THE UNION. Publishing a Turnkey term as
        # though it covered the Exterior Finished price too would be exactly
        # the quiet widening this contract exists to prevent. Only what is
        # true of EVERY priced configuration reaches the product level, in
        # anchor order so the sequence cannot be changed by a curator
        # rewriting a sentence.
        common = None
        for c in configs:
            t = set(c.get("terms") or ())
            common = t if common is None else (common & t)
        shared = [t for t, _ in COMMERCIAL_TERM_ANCHORS if t in (common or set())]

        extra = {"basis": basis, "vatRatePercent": rate}
        if shared:
            extra["commercialTerms"] = shared
        if len(configs) > 1 or configs[0]["label"]:
            extra["configurations"] = configs

        # The scalar is RETAINED, not deprecated, and is always the LOWEST
        # configuration. Founder decision 2. Every existing consumer keeps
        # working and shows the entry price rather than an arbitrary one.
        # Founder decision 3 governs how it may be LABELLED: never as an
        # unqualified turnkey or completed-home price. That is enforced at the
        # reader, and asserted by PG10.
        return ("VERIFIED_NUMERIC_PRICE", configs[0]["amount"],
                txt(cell(first, "Currency")) or None,
                configs[0]["priceType"], extra)

    for r in price_rows:
        ptype = txt(cell(r, "Price Type"))
        if ptype.lower() in QUOTE_TYPES:
            best = ("EVIDENCED_POA_QUOTE", None,
                    txt(cell(r, "Currency")) or None, ptype, {})
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

    price_state, amount, currency, ptype, price_extra = _price_state(price_rows)
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
        "price": dict({"state": price_state, "amount": amount,
                       "currency": currency, "priceType": ptype},
                      **price_extra),
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
    # ACCEPTED_CEILING_AREA_BASES. `abs()` is deliberately not used — a product below
    # the ceiling by more than the tolerance is not at the edge, and one above
    # the ceiling never reaches here at all.
    if (BAND_MAX - n) <= BAND_EDGE_TOLERANCE_M2 and basis not in ACCEPTED_CEILING_AREA_BASES:
        # HELD FROM THE PATHWAY ONLY. The product remains an Additional Home,
        # remains CONFIRMED RESIDENTIAL HABITATION, remains ELIGIBLE, and keeps
        # its Irish availability and price evidence untouched.
        return {"state": "HELD",
                "reason": "area-basis-insufficient-for-ceiling-test",
                "caveats": ["area-basis-insufficient-for-ceiling-test"]}
    return {"state": "CANDIDATE", "reason": None, "caveats": caveats}
