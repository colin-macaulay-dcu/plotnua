#!/usr/bin/env python3
"""
PlotNua — PARKING PLATFORM evidence manifest GENERATOR (controlled pilot).

    generate_parking_platform_evidence.py [--out FILE] [--as-of YYYY-MM-DD]

Emits `parking-platform-evidence.json`.

WHAT THIS PILOT IS FOR.

  To test whether PlotNua can represent a real NON-PRODUCT homeowner route
  without forcing it into the Garden Room PRODUCT architecture. A parking
  platform is not a product: it has no dimensions, no delivery date and no
  price of its own. What it has is a set of TERMS, and terms change. The
  Garden Room evidence layer has no validity window anywhere in it, so terms
  cannot live there honestly.

  This manifest follows the architecture already proven by
  `plotnua.driveway.evidence.v1` and disc026: a claim is the unit, every claim
  carries its own source, its own verification date and its own recheck
  interval, and staleness is resolved HERE, once, never in the browser.

THE SEPARATION THIS EXISTS TO ENFORCE.

  PUBLIC_PRIMARY evidence        — what the platform publishes to the world.
  SUPPLIER_PROVIDED evidence     — what the platform tells PlotNua directly.
  COMMERCIAL_CORRESPONDENCE      — our relationship with them.

  These are three different things and the third proves nothing about the
  first. A positive reply from a partnerships team is not evidence that an
  Irish homeowner can list a space, what it costs, or whether they are
  insured. `provenance` keeps them apart permanently, so a later fact supplied
  by the platform itself can be added without ever being mistaken for one we
  verified independently.

WHAT IS DELIBERATELY NOT HERE.

  No host commission rate  — not published anywhere; inferring one would be
                             inventing the homeowner's economics.
  No ROI host insurance    — absent from all three Irish documents. The UK
                             terms carry a clause limiting cover to residents
                             of the UK, Channel Islands and Isle of Man. That
                             clause is UK evidence and is explicitly forbidden
                             from being read across (see prohibited_readings).
  No Eircode onboarding    — the signup flow was not completed, because that
                             would require creating an account. Documentary
                             evidence is strong; it is not the same thing, and
                             is recorded as UNKNOWN rather than assumed.

  Atlas exists to record uncertainty accurately, not to remove it by guessing.

Edit the records below; never hand-edit the JSON.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime
from pathlib import Path

SCHEMA = "plotnua.parking-platform.evidence.v1"
JURISDICTION = "IE-ROI"

# ── evidence states ─────────────────────────────────────────────────────────
# VERIFIED                 PlotNua read the primary document itself.
# SUPPLIER-CLAIMED         The platform asserts it; nobody independent confirms.
# UNKNOWN                  Looked for, not found, or not testable without an act
#                          PlotNua will not perform. NEVER equals false.
# NOT_PUBLICLY_EVIDENCED   Searched the primary documents; the claim is absent.
# CONTRADICTED             The platform's own sources disagree with each other.
STATES = {"VERIFIED", "SUPPLIER-CLAIMED", "UNKNOWN",
          "NOT_PUBLICLY_EVIDENCED", "CONTRADICTED"}

PROVENANCE = {"PUBLIC_PRIMARY", "SUPPLIER_PROVIDED", "COMMERCIAL_CORRESPONDENCE"}

# ── sources ─────────────────────────────────────────────────────────────────
S_TERMS_IE = ("YourParkingSpace.ie — Terms & Conditions",
              "https://www.yourparkingspace.ie/company/terms-conditions")
S_CONTRACT_IE = ("YourParkingSpace.ie — Parking Contract",
                 "https://www.yourparkingspace.ie/company/parking-contract")
S_LIST_IE = ("YourParkingSpace.ie — List your space",
             "https://www.yourparkingspace.ie/list-your-space")
S_HOME_IE = ("YourParkingSpace.ie — Home / FAQ",
             "https://www.yourparkingspace.ie/")
S_SUPPORT_IE = ("YourParkingSpace.ie — Space Owner FAQs",
                "https://www.yourparkingspace.ie/support/space-owners-201159225/"
                "listing-my-space-202613485/")
S_TERMS_UK = ("YourParkingSpace.co.uk — Terms & Conditions",
              "https://www.yourparkingspace.co.uk/company/terms-conditions")

VERIFIED_ON = "2026-09-22"

PLATFORM = {
    "platform_key": "yourparkingspace-ie",
    "platform_name": "YourParkingSpace",
    "legal_entity": "YourParkingSpace (Ireland) Limited",
    "atlas_organisation_code": "ORG-YPS-IE",
    "jurisdiction": JURISDICTION,
    "route": "Homeowner lists a private parking space",
    "pilot": True,
    "pilot_note": (
        "Controlled architectural pilot. One platform only. Not a catalogue "
        "entry, not a recommendation, and not homeowner-facing."
    ),
}


def claim(key, text, value, state, provenance, source, quote=None,
          months=6, method="PRIMARY_FETCH", homeowner_safe=True,
          logic_safe=True, triggers=None, prohibited=None, notes=None):
    title, url = source
    return {
        "claim_key": key,
        "claim": text,
        "value": value,
        "evidence_state": state,
        "provenance": provenance,
        "source_title": title,
        "source_url": url,
        "quote": quote,
        "last_verified": VERIFIED_ON,
        "review_interval_months": months,
        "verification_method": method,
        "staleness_policy": "DOWNGRADE",
        "recheck_triggers": triggers or [],
        "prohibited_readings": prohibited or [],
        "homeowner_safe": homeowner_safe,
        "logic_safe": logic_safe,
        "notes": notes,
    }


CLAIMS = [
    # ── identity ────────────────────────────────────────────────────────────
    claim("platform_legal_identity",
          "The Irish service is operated by a separate Irish-registered company.",
          {"entity": "YourParkingSpace (Ireland) Limited",
           "registration": "700209", "vat": "03790129TH",
           "address": "Office 23, The Cranford Centre, Montrose, Dublin, D04X6H0"},
          "VERIFIED", "PUBLIC_PRIMARY", S_TERMS_IE,
          quote=("We are YourParkingSpace (Ireland) Limited, a company registered "
                 "in Ireland. Our company registration number is 700209"),
          months=12,
          triggers=["The .ie terms name a different operating entity."],
          notes="Identity is durable; it is the claims below that expire."),

    claim("governing_law",
          "The Irish terms are governed by Irish law, in the Irish courts.",
          {"law": "Irish", "courts": "Irish"},
          "VERIFIED", "PUBLIC_PRIMARY", S_TERMS_IE,
          quote=("These terms are governed by Irish law and either party can "
                 "bring legal proceedings in the Irish courts."),
          months=12,
          prohibited=["Any reading that the UK terms (English law) govern an "
                      "Irish homeowner."]),

    claim("company_number_inconsistency",
          "The .ie site footer shows the UK company number while the .ie terms "
          "name the Irish entity.",
          {"footer_shows": "08670309 (UK)", "terms_state": "700209 (IE)"},
          "CONTRADICTED", "PUBLIC_PRIMARY", S_LIST_IE,
          quote="Company No. 08670309 | YourParkingSpace © 2026",
          months=6, homeowner_safe=False, logic_safe=False,
          notes=("Recorded, not resolved. Does not undermine the Irish entity "
                 "evidence in the terms; it does mean the site is not internally "
                 "consistent about which company a homeowner contracts with."),
          triggers=["The .ie footer changes."]),

    # ── the homeowner route ─────────────────────────────────────────────────
    claim("irish_homeowner_listing_route",
          "The Irish terms expressly provide for a user advertising a parking "
          "space, and define a Private Space Owner at private property.",
          {"section": "LISTING A PARKING SPACE",
           "role": "Space Owner / Private Space Owner"},
          "VERIFIED", "PUBLIC_PRIMARY", S_TERMS_IE,
          quote=("The terms in this section only apply to you if you advertise "
                 "a parking space using the Online Service."),
          months=6,
          triggers=["The listing section is removed from the .ie terms."]),

    claim("host_onboarding_route_available",
          "A host onboarding page is served on the Irish domain.",
          {"url": S_LIST_IE[1], "state": "live"},
          "VERIFIED", "PUBLIC_PRIMARY", S_LIST_IE,
          quote="Start earning money as a YourParkingSpace host.",
          months=3,
          triggers=["The .ie list-your-space page 404s or redirects to .co.uk."],
          notes="Page availability only. Not proof a listing completes."),

    claim("eircode_onboarding_accepted",
          "Whether the listing flow accepts an Irish address / Eircode.",
          None, "UNKNOWN", "PUBLIC_PRIMARY", S_LIST_IE,
          months=3, homeowner_safe=False, logic_safe=False,
          prohibited=["Any reading that onboarding succeeds because the page "
                      "exists, or because the entity is Irish."],
          notes=("NOT TESTED BY DESIGN. Completing signup would require creating "
                 "an account, which PlotNua does not do during evidence work. "
                 "UNKNOWN is the honest state, not a gap to be filled by "
                 "assumption.")),

    claim("homeowner_eligibility",
          "Private individuals advertising a space at private property are a "
          "defined category in the Irish terms.",
          {"category": "Private Space Owner",
           "basis": "private property not used in the course of a business"},
          "VERIFIED", "PUBLIC_PRIMARY", S_TERMS_IE, months=6),

    claim("space_property_requirements",
          "Published minimum requirements for a listable space (dimensions, "
          "access, surface, permit status).",
          None, "NOT_PUBLICLY_EVIDENCED", "PUBLIC_PRIMARY", S_TERMS_IE,
          months=6,
          notes=("The .ie Space Owner FAQ lists 'My space requires a permit, can "
                 "I list?' as a question, but the Irish help centre returns no "
                 "articles.")),

    claim("ie_space_owner_knowledge_base",
          "The Irish help centre holds no Space Owner articles.",
          {"articles": 0}, "VERIFIED", "PUBLIC_PRIMARY", S_SUPPORT_IE,
          quote="View all 0 results",
          months=3, homeowner_safe=False,
          notes="Evidence of an information gap, not of unavailability."),

    # ── money ───────────────────────────────────────────────────────────────
    claim("listing_cost",
          "Listing a space is advertised as free.",
          {"cost": "free to list"},
          "SUPPLIER-CLAIMED", "PUBLIC_PRIMARY", S_LIST_IE,
          quote="100% free to list", months=6),

    claim("host_fee_model",
          "The platform fee is added to the Driver's price ON TOP of the price "
          "the Space Owner sets — a driver-side markup, not a deduction from "
          "host earnings.",
          {"model": "markup added to Space Owner's set price, charged to Driver"},
          "VERIFIED", "PUBLIC_PRIMARY", S_TERMS_IE,
          quote=("The price advertised on the Online Service includes our fee "
                 "that that we charge on top of the Space Owner's set price"),
          months=6,
          notes=("Structurally different from a commission. It determines what a "
                 "homeowner actually receives, so the STRUCTURE is recorded even "
                 "though the RATE is not published.")),

    claim("host_fee_rate",
          "The rate or percentage of the platform fee.",
          None, "NOT_PUBLICLY_EVIDENCED", "PUBLIC_PRIMARY", S_TERMS_IE,
          months=6, homeowner_safe=False, logic_safe=False,
          prohibited=["Any percentage taken from a third-party article, a "
                      "competitor, the UK site, or an estimate."],
          notes="The single largest gap in the homeowner economics."),

    claim("payment_mechanism",
          "Earnings are paid monthly by bank deposit.",
          {"frequency": "monthly", "method": "bank deposit"},
          "SUPPLIER-CLAIMED", "PUBLIC_PRIMARY", S_LIST_IE,
          quote=("Each month, we will deposit the earnings directly into your "
                 "bank account."), months=6),

    claim("vat_treatment",
          "Prices for parking and for listing are inclusive of applicable VAT.",
          {"vat": "inclusive"}, "VERIFIED", "PUBLIC_PRIMARY", S_TERMS_IE,
          months=12),

    claim("chargeback_admin_fee",
          "A chargeback attracts a euro-denominated administration fee.",
          {"amount": 15.00, "currency": "EUR"},
          "VERIFIED", "PUBLIC_PRIMARY", S_CONTRACT_IE,
          quote="a €15.00 administration fee will be applied to the booking",
          months=6,
          notes="Evidence the Irish contract is euro-denominated in its own right."),

    claim("host_price_change_notice",
          "A Space Owner must give 30 days' notice to change their price.",
          {"notice_days": 30}, "VERIFIED", "PUBLIC_PRIMARY", S_TERMS_IE,
          quote="must provide us with 30 days' notice for such change to take effect",
          months=6),

    # ── obligations and protections ─────────────────────────────────────────
    claim("cancellation_terms",
          "A published cancellation and refund policy applies to both parties.",
          {"hourly_daily": "100% refund if cancelled >24h before start; none inside 24h",
           "monthly": "full refund if >=48h before start; 7 days' notice to stop renewal",
           "season": "30 days' notice to stop renewal",
           "space_owner": "may cancel; must contact the platform as soon as possible"},
          "VERIFIED", "PUBLIC_PRIMARY", S_CONTRACT_IE, months=6),

    claim("anti_circumvention_restriction",
          "A Private Space Owner appoints the platform as agent and may not take "
          "a driver introduced by the platform off-platform.",
          {"agency": True, "circumvention": "restricted"},
          "VERIFIED", "PUBLIC_PRIMARY", S_TERMS_IE,
          months=6,
          notes="A real homeowner obligation, easy to miss and worth surfacing."),

    claim("host_protection_insurance_roi",
          "Host protection or insurance cover for an Irish Space Owner.",
          None, "NOT_PUBLICLY_EVIDENCED", "PUBLIC_PRIMARY", S_TERMS_IE,
          months=3, homeowner_safe=False, logic_safe=False,
          prohibited=[
              "Reading the UK insurance schedule across to Ireland. The UK terms "
              "state cover requires a main residence within the United Kingdom, "
              "Channel Islands or Isle of Man — which is UK evidence about a UK "
              "product, and says nothing about Ireland either way.",
              "Any statement to a homeowner that they are, or are not, covered."],
          notes=("Searched the .ie Terms, the .ie Parking Contract and the .ie "
                 "host page: the word 'insurance' does not appear in any of "
                 "them. Absent, not refused.")),

    claim("space_verification_requirements",
          "What verification the platform performs on a listed space.",
          None, "NOT_PUBLICLY_EVIDENCED", "PUBLIC_PRIMARY", S_TERMS_IE,
          months=6,
          quote=("whilst we use reasonable efforts to verify the accuracy of such "
                 "information we offer no warranty in relation to these details"),
          notes=("The terms disclaim warranty over Space Owner details; they do "
                 "not describe a verification process.")),

    claim("referral_affiliate_route",
          "A published referral or affiliate programme open to PlotNua.",
          None, "NOT_PUBLICLY_EVIDENCED", "PUBLIC_PRIMARY", S_HOME_IE,
          months=6,
          notes="No affiliate or partner-signup route located on the .ie site."),

    # ── coverage ────────────────────────────────────────────────────────────
    claim("ireland_service_coverage",
          "The platform states it covers Ireland alongside the UK.",
          {"statement": "over 350,000 spaces across the UK and Ireland"},
          "SUPPLIER-CLAIMED", "PUBLIC_PRIMARY", S_HOME_IE,
          quote=("The YourParkingSpace platform connects drivers with over "
                 "350,000 privately owned and commercially operated parking "
                 "spaces across the UK and Ireland"),
          months=6,
          prohibited=["Any per-county or per-town Irish coverage claim. The "
                      "figure is combined UK-and-Ireland and is not broken down."],
          notes=("A first-party marketing claim. Irish driver testimonials naming "
                 "Dublin, Cork and Mayo are published alongside it, which "
                 "corroborates Irish activity but does not verify the number.")),

    # ── relationship, kept strictly apart ───────────────────────────────────
    claim("plotnua_commercial_relationship",
          "PlotNua's outreach received a positive response and was escalated "
          "internally to a Head of Partnerships; contact is awaited.",
          {"state": "POSITIVE RESPONSE — ESCALATED INTERNALLY TO HEAD OF "
                    "PARTNERSHIPS — AWAITING CONTACT",
           "escalated_to_role": "Head of Partnerships"},
          "SUPPLIER-CLAIMED", "COMMERCIAL_CORRESPONDENCE",
          ("PlotNua outreach record (not a public source)", None),
          months=3, homeowner_safe=False, logic_safe=False,
          method="CORRESPONDENCE",
          prohibited=[
              "Any reading that this establishes service availability, fees, "
              "insurance, eligibility, coverage or any homeowner-facing claim.",
              "Any homeowner-facing use whatsoever."],
          notes=("Relationship evidence only. Carried here so it is on the record "
                 "with its provenance visible, and so it can never be silently "
                 "mistaken for a verified service fact.")),
]


# States that may never drive logic, whatever an author hand-sets. The pilot's
# own test suite caught three claims where this had been left to per-claim
# judgement and applied inconsistently — so it is now DERIVED, not trusted.
NEVER_LOGIC_SAFE = {"UNKNOWN", "NOT_PUBLICLY_EVIDENCED", "CONTRADICTED"}


def resolve(as_of: date, c: dict) -> dict:
    """Staleness resolved HERE, once, never in the browser."""
    lv = datetime.strptime(c["last_verified"], "%Y-%m-%d").date()
    months = (as_of.year - lv.year) * 12 + (as_of.month - lv.month)
    if as_of.day < lv.day:
        months -= 1
    due = months >= c["review_interval_months"]
    out = dict(c)
    out["months_since_verified"] = max(months, 0)
    out["verification_status"] = "STALE" if due else "CURRENT"

    # LOGIC SAFETY IS DERIVED, NEVER HAND-SET.
    # An absence of evidence can never be an input to a decision. That holds
    # however carefully the claim is written, and however safe it is to SHOW.
    # Correspondence is excluded too: our relationship with a platform is not
    # a fact about the platform's service.
    logic = (bool(c["logic_safe"])
             and not due
             and c["evidence_state"] not in NEVER_LOGIC_SAFE
             and c["provenance"] != "COMMERCIAL_CORRESPONDENCE")
    out["logic_safe_resolved"] = logic

    # HOMEOWNER SAFETY IS DIFFERENT, DELIBERATELY.
    # "PlotNua could not find a published fee rate" is honest and useful, so an
    # UNKNOWN may be shown. What may never be shown is an unknown dressed as a
    # fact — which is why value stays null and the state travels with it. Only
    # correspondence and contradictions are withheld outright.
    out["homeowner_safe_resolved"] = (
        bool(c["homeowner_safe"])
        and not due
        and c["provenance"] != "COMMERCIAL_CORRESPONDENCE"
    )
    return out


def build(as_of: date) -> dict:
    claims = [resolve(as_of, c) for c in CLAIMS]
    by_state = {}
    for c in claims:
        by_state[c["evidence_state"]] = by_state.get(c["evidence_state"], 0) + 1
    by_prov = {}
    for c in claims:
        by_prov[c["provenance"]] = by_prov.get(c["provenance"], 0) + 1
    return {
        "schema": SCHEMA,
        "generated": as_of.isoformat(),
        "jurisdiction": JURISDICTION,
        "pilot": True,
        "platformCount": 1,
        "platforms": [PLATFORM],
        "claimCount": len(claims),
        "claimsByState": by_state,
        "claimsByProvenance": by_prov,
        "homeownerSafeCount": sum(1 for c in claims if c["homeowner_safe_resolved"]),
        "note": (
            "Generated by .github/scripts/generate_parking_platform_evidence.py. "
            "Do not hand-edit. Staleness is resolved at generation time. This "
            "manifest is NOT homeowner-facing and is NOT wired to any runtime: "
            "it is a controlled architectural pilot. No Atlas Product record, "
            "Product Category or Product Type was created or modified for it."
        ),
        "claims": claims,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="parking-platform-evidence.json")
    ap.add_argument("--as-of", default=None)
    a = ap.parse_args()
    as_of = (datetime.strptime(a.as_of, "%Y-%m-%d").date() if a.as_of
             else date.today())

    for c in CLAIMS:
        if c["evidence_state"] not in STATES:
            print(f"FAIL: bad evidence_state {c['evidence_state']!r}", file=sys.stderr)
            return 1
        if c["provenance"] not in PROVENANCE:
            print(f"FAIL: bad provenance {c['provenance']!r}", file=sys.stderr)
            return 1

    payload = build(as_of)
    Path(a.out).write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
                           encoding="utf-8")
    print(f"  wrote {a.out}")
    print(f"  platform  {PLATFORM['legal_entity']}")
    print(f"  claims    {payload['claimCount']}")
    for k, v in sorted(payload["claimsByState"].items()):
        print(f"    {k:<24} {v}")
    print(f"  homeowner-safe claims: {payload['homeownerSafeCount']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
