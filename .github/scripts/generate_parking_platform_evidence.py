#!/usr/bin/env python3
"""
PlotNua — PARKING PLATFORM evidence manifest GENERATOR (controlled pilot).

    generate_parking_platform_evidence.py [--out FILE] [--as-of YYYY-MM-DD]

CANONICAL EVIDENCE MODEL — GOVERNANCE CORRECTION, 2026-09-22.

  The first draft of this pilot introduced a flat `evidence_state` field
  (VERIFIED / SUPPLIER-CLAIMED / ...) and dropped the decomposition the
  existing manifests have always used. One word was left carrying what six
  fields carried in plotnua.driveway.evidence.v1 and plotnua.disc026.
  evidence.v1, and "VERIFIED" read like "PlotNua established this is true"
  while actually meaning "a primary source currently states this".

  The house decomposition is canonical and is restored here:

      authority            who states it
      source_type          in what kind of instrument
      evidence_type        what kind of evidence this is
      verification_method  how PlotNua checked
      verification_status  whether that check is still fresh
      maturity             the real-world standing of what is claimed
      validity/staleness   valid_from / review_interval / resolved status
      provenance           public primary | supplier-provided | correspondence
      homeowner_safe       may this be shown
      logic_safe           may this drive a decision

  `evidence_state` still appears in the artefact, but it is now DERIVED at
  generation time from source_type, evidence_type and provenance. It is a
  display label, never the stored truth. Change the underlying dimensions and
  the label follows; it can no longer be hand-set to say something the
  evidence does not support.

THE NEW AXIS — claim_basis.

      STATED       PlotNua established that the cited authoritative, primary
                   or first-party source CURRENTLY STATES or PROVIDES this.
      OPERATIONAL  PlotNua has evidence the claimed behaviour ACTUALLY OCCURS
                   or operates in practice.

  STATED is NOT a weaker grade. For legislation, contractual terms and other
  operative instruments the published text IS the operative thing: a parking
  contract does not describe the cancellation policy, it constitutes it. Such
  claims are legitimately decision-useful and logic-safe.

  What STATED does not do is establish behaviour. "The contract provides 30
  days' notice" and "the platform applies 30 days' notice" are different
  claims, and only the first is evidenced here.

  EVERY claim in this manifest is STATED. Not one is OPERATIONAL, because
  PlotNua holds no operational evidence about any platform. Recording that
  explicitly is the point of the axis.

Edit the records below; never hand-edit the JSON.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime
from pathlib import Path

SCHEMA = "plotnua.parking-platform.evidence.v2"
JURISDICTION = "IE-ROI"
VERIFIED_ON = "2026-09-22"

# ── canonical vocabularies ──────────────────────────────────────────────────
CLAIM_BASIS = {"STATED", "OPERATIONAL"}

EVIDENCE_TYPE = {
    "PUBLISHED_SOURCE",     # the source publishes it
    "ABSENCE_OF_RECORD",    # searched a stated scope; not present
    "CONFLICTING_SOURCES",  # the provider's own sources disagree
    "UNTESTED",             # not establishable without an act PlotNua won't take
    "CORRESPONDENCE",       # told to PlotNua directly
}

SOURCE_TYPE = {
    "CONTRACT_TERM",        # operative instrument: terms, parking contract
    "CORPORATE_REGISTER",   # identity as filed/published
    "PROVIDER_PAGE",        # provider's own functional page
    "MARKETING_CLAIM",      # provider's own promotional assertion
    "SUPPORT_CONTENT",      # provider's help centre
    "OUTREACH_RECORD",      # PlotNua's correspondence
}

PROVENANCE = {"PUBLIC_PRIMARY", "SUPPLIER_PROVIDED", "COMMERCIAL_CORRESPONDENCE"}

MATURITY = {
    "IN_FORCE",             # currently published and operative
    "CURRENT_PUBLISHED",    # currently published, not operative in itself
    "BOUNDED_SEARCH",       # the claim is the result of a scoped search
    "NOT_ESTABLISHABLE",    # cannot be established by the means available
    "UNRESOLVED_CONFLICT",  # sources disagree; not adjudicated
}

NEVER_LOGIC_SAFE_TYPES = {"ABSENCE_OF_RECORD", "UNTESTED", "CONFLICTING_SOURCES"}

# ── sources ─────────────────────────────────────────────────────────────────
ENTITY = "YourParkingSpace (Ireland) Limited"
S_TERMS = ("YourParkingSpace.ie — Terms & Conditions",
           "https://www.yourparkingspace.ie/company/terms-conditions")
S_CONTRACT = ("YourParkingSpace.ie — Parking Contract",
              "https://www.yourparkingspace.ie/company/parking-contract")
S_LIST = ("YourParkingSpace.ie — List your space",
          "https://www.yourparkingspace.ie/list-your-space")
S_HOME = ("YourParkingSpace.ie — Home / platform FAQ",
          "https://www.yourparkingspace.ie/")
S_SUPPORT = ("YourParkingSpace.ie — Space Owner FAQs",
             "https://www.yourparkingspace.ie/support/space-owners-201159225/"
             "listing-my-space-202613485/")
   # (No outreach source is referenced. Private correspondence is not a source
   # for a publicly served artefact — see the note in CLAIMS below.)

PLATFORM = {
    "platform_key": "yourparkingspace-ie",
    "platform_name": "YourParkingSpace",
    "legal_entity": ENTITY,
    # Airtable record IDs are internal join keys and are deliberately NOT
    # emitted into a publicly fetchable artefact. PlotNua's own scheme code is
    # kept: it identifies the organisation without exposing anything about the
    # internal base.
    "atlas_organisation_code": "ORG-YPS-IE",
    "jurisdiction": JURISDICTION,
    "route": "Homeowner lists a private parking space",
    "pilot": True,
    "pilot_note": (
        "Controlled architectural pilot. One platform only. Not a catalogue "
        "entry, not a recommendation, not runtime-connected, and not "
        "homeowner-facing."
    ),
}

# ── the conceptual completion model (recorded, never mechanically scored) ───
COMPLETION_MODEL = {
    "dimensions": [
        "Identity", "Route", "Jurisdiction", "Commercial Terms",
        "Protection", "Exit", "Currency",
    ],
    "rule": (
        "A VERIFIED or EVIDENCED NEGATIVE may satisfy a dimension — 'this "
        "platform offers no host protection', established, is an answer. "
        "UNKNOWN does not satisfy a dimension."
    ),
    "completion_means": (
        "PlotNua has enough current evidence across the decision-critical "
        "dimensions for a homeowner to understand the route, the material "
        "terms, the material protections and limitations, and the material "
        "remaining uncertainty, sufficiently to make the next decision."
    ),
    "explicitly_not": (
        "NOT a mechanical 7-of-7 count. A non-critical unknown does not "
        "prevent usefulness; a decision-critical unknown may prevent "
        "completion. Completion is a judgement against the sentence above, "
        "made by a person, not a score computed by this file."
    ),
}


def claim(key, text, value, *, basis, evidence_type, source_type, provenance,
          maturity, source, authority=ENTITY, quote=None, months=6,
          method="PRIMARY_FETCH", homeowner_safe=True, logic_safe=True,
          triggers=None, prohibited=None, notes=None):
    title, url = source
    return {
        "claim_key": key,
        "claim": text,
        "value": value,
        "claim_basis": basis,
        "authority": authority,
        "source_type": source_type,
        "evidence_type": evidence_type,
        "maturity": maturity,
        "provenance": provenance,
        "verification_method": method,
        "source_title": title,
        "source_url": url,
        "quote": quote,
        "last_verified": VERIFIED_ON,
        "valid_from": VERIFIED_ON,
        "valid_until": None,
        "review_interval_months": months,
        "staleness_policy": "DOWNGRADE",
        "recheck_triggers": triggers or [],
        "prohibited_readings": prohibited or [],
        "homeowner_safe": homeowner_safe,
        "logic_safe": logic_safe,
        "notes": notes,
    }


# Shorthands for the three recurring shapes.
def stated(key, text, value, source, source_type, maturity, **kw):
    return claim(key, text, value, basis="STATED",
                 evidence_type="PUBLISHED_SOURCE", source_type=source_type,
                 provenance="PUBLIC_PRIMARY", maturity=maturity,
                 source=source, **kw)


def absent(key, text, source, **kw):
    kw.setdefault("logic_safe", False)
    kw.setdefault("homeowner_safe", True)
    return claim(key, text, None, basis="STATED",
                 evidence_type="ABSENCE_OF_RECORD", source_type="CONTRACT_TERM",
                 provenance="PUBLIC_PRIMARY", maturity="BOUNDED_SEARCH",
                 method="TARGETED_SEARCH", source=source, **kw)


CLAIMS = [
    # ── Identity ────────────────────────────────────────────────────────────
    stated("platform_legal_identity",
           "The Irish service is operated by a separate Irish-registered company.",
           {"entity": ENTITY, "registration": "700209", "vat": "03790129TH",
            "address": "Office 23, The Cranford Centre, Montrose, Dublin, D04X6H0"},
           S_TERMS, "CORPORATE_REGISTER", "IN_FORCE", months=12,
           quote=("We are YourParkingSpace (Ireland) Limited, a company "
                  "registered in Ireland. Our company registration number is "
                  "700209"),
           triggers=["The .ie terms name a different operating entity."],
           notes="Identity is durable; the terms below are not."),

    claim("company_number_inconsistency",
          "The .ie site footer shows the UK company number while the .ie terms "
          "name the Irish entity.",
          {"footer_shows": "08670309 (UK)", "terms_state": "700209 (IE)"},
          basis="STATED", evidence_type="CONFLICTING_SOURCES",
          source_type="PROVIDER_PAGE", provenance="PUBLIC_PRIMARY",
          maturity="UNRESOLVED_CONFLICT", source=S_LIST,
          quote="Company No. 08670309 | YourParkingSpace © 2026",
          homeowner_safe=False, logic_safe=False,
          triggers=["The .ie footer changes."],
          notes=("Recorded, not adjudicated. Does not undermine the Irish "
                 "entity evidence in the terms; it does mean the site is not "
                 "internally consistent about which company a homeowner "
                 "contracts with.")),

    # ── Jurisdiction ────────────────────────────────────────────────────────
    stated("governing_law",
           "The Irish terms are governed by Irish law, in the Irish courts.",
           {"law": "Irish", "courts": "Irish"},
           S_TERMS, "CONTRACT_TERM", "IN_FORCE", months=12,
           quote=("These terms are governed by Irish law and either party can "
                  "bring legal proceedings in the Irish courts."),
           prohibited=["Any reading that the UK terms (English law) govern an "
                       "Irish homeowner."]),

    # ── Route ───────────────────────────────────────────────────────────────
    stated("irish_homeowner_listing_route",
           "The Irish terms expressly provide for a user advertising a parking "
           "space, and define a Private Space Owner at private property.",
           {"section": "LISTING A PARKING SPACE",
            "role": "Space Owner / Private Space Owner"},
           S_TERMS, "CONTRACT_TERM", "IN_FORCE",
           quote=("The terms in this section only apply to you if you advertise "
                  "a parking space using the Online Service."),
           triggers=["The listing section is removed from the .ie terms."]),

    stated("host_onboarding_page_available",
           "A host onboarding page is served on the Irish domain.",
           {"url": S_LIST[1], "state": "live"},
           S_LIST, "PROVIDER_PAGE", "CURRENT_PUBLISHED", months=3,
           quote="Start earning money as a YourParkingSpace host.",
           triggers=["The .ie list-your-space page 404s or redirects to .co.uk."],
           notes=("Page availability only. STATED, not OPERATIONAL: it does not "
                  "establish that a listing completes.")),

    claim("eircode_onboarding_accepted",
          "Whether the listing flow accepts an Irish address / Eircode.",
          None, basis="STATED", evidence_type="UNTESTED",
          source_type="PROVIDER_PAGE", provenance="PUBLIC_PRIMARY",
          maturity="NOT_ESTABLISHABLE", source=S_LIST,
          method="NOT_ATTEMPTED", months=3,
          homeowner_safe=True, logic_safe=False,
          prohibited=["Any reading that onboarding succeeds because the page "
                      "exists, or because the entity is Irish."],
          notes=("NOT TESTED BY DESIGN. Completing signup would require "
                 "creating an account, which PlotNua does not do during "
                 "evidence work. This is the clearest case in the manifest of "
                 "a claim that could only ever be settled OPERATIONALLY.")),

    stated("homeowner_eligibility",
           "Private individuals advertising a space at private property are a "
           "defined category in the Irish terms.",
           {"category": "Private Space Owner",
            "basis": "private property not used in the course of a business"},
           S_TERMS, "CONTRACT_TERM", "IN_FORCE"),

    absent("space_property_requirements",
           "Published minimum requirements for a listable space (dimensions, "
           "access, surface, permit status).", S_TERMS,
           notes=("The .ie Space Owner FAQ lists 'My space requires a permit, "
                  "can I list?' as a question, but the Irish help centre "
                  "returns no articles.")),

    stated("ie_space_owner_knowledge_base",
           "The Irish help centre holds no Space Owner articles.",
           {"articles": 0}, S_SUPPORT, "SUPPORT_CONTENT", "CURRENT_PUBLISHED",
           months=3, homeowner_safe=False,
           quote="View all 0 results",
           notes="Evidence of an information gap, not of unavailability."),

    # ── Commercial Terms ────────────────────────────────────────────────────
    stated("listing_cost",
           "Listing a space is advertised as free.", {"cost": "free to list"},
           S_LIST, "MARKETING_CLAIM", "CURRENT_PUBLISHED",
           quote="100% free to list"),

    stated("host_fee_model",
           "The platform fee is added to the Driver's price ON TOP of the price "
           "the Space Owner sets — a driver-side markup, not a deduction from "
           "host earnings.",
           {"model": "markup added to Space Owner's set price, charged to Driver"},
           S_TERMS, "CONTRACT_TERM", "IN_FORCE",
           quote=("The price advertised on the Online Service includes our fee "
                  "that that we charge on top of the Space Owner's set price"),
           notes=("Structurally different from a commission. STATED in an "
                  "operative instrument, so decision-useful; the RATE is a "
                  "separate claim and is not evidenced.")),

    absent("host_fee_rate",
           "The rate or percentage of the platform fee.", S_TERMS,
           homeowner_safe=True,
           prohibited=["Any percentage taken from a third-party article, a "
                       "competitor, the UK site, or an estimate."],
           notes=("Searched the .ie Terms, the .ie Parking Contract and the .ie "
                  "host page. DECISION-CRITICAL: a homeowner cannot work out "
                  "what they receive without it.")),

    stated("payment_mechanism",
           "Earnings are paid monthly by bank deposit.",
           {"frequency": "monthly", "method": "bank deposit"},
           S_LIST, "MARKETING_CLAIM", "CURRENT_PUBLISHED",
           quote=("Each month, we will deposit the earnings directly into your "
                  "bank account."),
           notes=("STATED on a provider page, not an operative term, and not "
                  "OPERATIONAL: no payment has been observed.")),

    stated("vat_treatment",
           "Prices for parking and for listing are inclusive of applicable VAT.",
           {"vat": "inclusive"}, S_TERMS, "CONTRACT_TERM", "IN_FORCE", months=12),

    stated("chargeback_admin_fee",
           "A chargeback attracts a euro-denominated administration fee.",
           {"amount": 15.00, "currency": "EUR"},
           S_CONTRACT, "CONTRACT_TERM", "IN_FORCE",
           quote="a €15.00 administration fee will be applied to the booking",
           notes=("Evidence the Irish contract is euro-denominated in its own "
                  "right, not a converted UK one.")),

    stated("host_price_change_notice",
           "A Space Owner must give 30 days' notice to change their price.",
           {"notice_days": 30}, S_TERMS, "CONTRACT_TERM", "IN_FORCE",
           quote=("must provide us with 30 days' notice for such change to take "
                  "effect")),

    # ── Exit ────────────────────────────────────────────────────────────────
    stated("cancellation_terms",
           "A published cancellation and refund policy applies to both parties.",
           {"hourly_daily": "100% refund if cancelled >24h before start; none inside 24h",
            "monthly": "full refund if >=48h before start; 7 days' notice to stop renewal",
            "season": "30 days' notice to stop renewal",
            "space_owner": "may cancel; must contact the platform as soon as possible"},
           S_CONTRACT, "CONTRACT_TERM", "IN_FORCE"),

    stated("anti_circumvention_restriction",
           "A Private Space Owner appoints the platform as agent and may not "
           "take a driver introduced by the platform off-platform.",
           {"agency": True, "circumvention": "restricted"},
           S_TERMS, "CONTRACT_TERM", "IN_FORCE",
           notes="A real homeowner obligation, easy to miss and worth surfacing."),

    # ── Protection ──────────────────────────────────────────────────────────
    absent("host_protection_insurance_roi",
           "Host protection or insurance cover for an Irish Space Owner.",
           S_TERMS, homeowner_safe=True, months=3,
           prohibited=[
               "Reading the UK insurance schedule across to Ireland. The UK "
               "terms state cover requires a main residence within the United "
               "Kingdom, Channel Islands or Isle of Man — UK evidence about a "
               "UK product, which says nothing about Ireland either way.",
               "Any statement to a homeowner that they are, or are not, covered."],
           notes=("Searched the .ie Terms, the .ie Parking Contract and the .ie "
                  "host page: the word 'insurance' does not appear in any of "
                  "them. Absent, not refused. DECISION-CRITICAL.")),

    absent("space_verification_requirements",
           "What verification the platform performs on a listed space.", S_TERMS,
           quote=("whilst we use reasonable efforts to verify the accuracy of "
                  "such information we offer no warranty in relation to these "
                  "details"),
           notes=("The terms disclaim warranty over Space Owner details; they "
                  "do not describe a verification process.")),

    absent("referral_affiliate_route",
           "A published referral or affiliate programme open to PlotNua.", S_HOME,
           notes="No affiliate or partner-signup route located on the .ie site."),

    # ── Coverage ────────────────────────────────────────────────────────────
    stated("ireland_service_coverage",
           "The platform states it covers Ireland alongside the UK.",
           {"statement": "over 350,000 spaces across the UK and Ireland"},
           S_HOME, "MARKETING_CLAIM", "CURRENT_PUBLISHED",
           quote=("The YourParkingSpace platform connects drivers with over "
                  "350,000 privately owned and commercially operated parking "
                  "spaces across the UK and Ireland"),
           logic_safe=False,
           prohibited=["Any per-county or per-town Irish coverage claim. The "
                       "figure is combined UK-and-Ireland with no breakdown."],
           notes=("A provider marketing claim, not an operative term. Irish "
                  "driver testimonials naming Dublin, Cork and Mayo are "
                  "published alongside it, which corroborates Irish activity "
                  "without verifying the number.")),

    # ── Relationship, kept strictly apart ───────────────────────────────────
    # ── NO COMMERCIAL CORRESPONDENCE CLAIM APPEARS HERE, DELIBERATELY ───────
    # This manifest is served from the repository root of a GitHub Pages site,
    # so every claim in it is publicly fetchable at plotnua.ie. PlotNua's
    # relationship with a platform — outreach status, negotiating position,
    # who at that company is expected to make contact — is private commercial
    # intelligence. It is not evidence about the platform's service, and it
    # must not become world-readable merely because an evidence artefact is
    # published.
    #
    # The PROVENANCE MODEL still carries COMMERCIAL_CORRESPONDENCE and
    # SUPPLIER_PROVIDED, and derive_state() and resolve() still handle both
    # correctly, so the firewall remains testable and a supplier-supplied fact
    # can still be added later without being mistaken for one PlotNua verified
    # independently. What is absent is the private INSTANCE, not the model.
    #
    # Relationship status stays where it already legitimately lives, in the
    # governed private record. Nothing was deleted from it by this file.
]


def derive_state(c: dict) -> str:
    """The display label. DERIVED, never stored as the primary truth.

    Change the underlying dimensions and this follows. It cannot be hand-set
    to assert something the evidence does not support — which is exactly how
    the first draft of this pilot went wrong.
    """
    et = c["evidence_type"]
    if et == "ABSENCE_OF_RECORD":
        return "NOT_PUBLICLY_EVIDENCED"
    if et == "UNTESTED":
        return "UNKNOWN"
    if et == "CONFLICTING_SOURCES":
        return "CONTRADICTED"
    if c["provenance"] == "COMMERCIAL_CORRESPONDENCE" or et == "CORRESPONDENCE":
        return "SUPPLIER-CLAIMED"
    # A published source. Whether it is the provider asserting something about
    # itself, or an operative instrument, is what separates the two.
    if c["source_type"] in ("MARKETING_CLAIM", "SUPPORT_CONTENT"):
        return "SUPPLIER-CLAIMED"
    return "VERIFIED"


def resolve(as_of: date, c: dict) -> dict:
    lv = datetime.strptime(c["last_verified"], "%Y-%m-%d").date()
    months = (as_of.year - lv.year) * 12 + (as_of.month - lv.month)
    if as_of.day < lv.day:
        months -= 1
    due = months >= c["review_interval_months"]

    out = dict(c)
    out["evidence_state_derived"] = derive_state(c)
    out["months_since_verified"] = max(months, 0)
    out["verification_status"] = "STALE" if due else "CURRENT"

    # LOGIC SAFETY IS DERIVED, NEVER HAND-SET.
    # An absence, an untested question or an unresolved conflict can never be
    # an input to a decision, however carefully written. Correspondence is
    # excluded too: our relationship with a provider is not a fact about the
    # provider's service. A STATED claim from an operative instrument CAN be
    # logic-safe — that is the point of keeping STATED a first-class basis.
    out["logic_safe_resolved"] = (
        bool(c["logic_safe"])
        and not due
        and c["evidence_type"] not in NEVER_LOGIC_SAFE_TYPES
        and c["provenance"] != "COMMERCIAL_CORRESPONDENCE"
    )
    # HOMEOWNER SAFETY IS DIFFERENT, DELIBERATELY. "PlotNua could not find a
    # published fee rate" is honest and worth showing. What may never be shown
    # is an unknown dressed as a fact — which is why value stays null and the
    # derived state travels with it.
    out["homeowner_safe_resolved"] = (
        bool(c["homeowner_safe"])
        and not due
        and c["provenance"] != "COMMERCIAL_CORRESPONDENCE"
    )
    return out


def build(as_of: date) -> dict:
    claims = [resolve(as_of, c) for c in CLAIMS]

    def tally(key):
        t = {}
        for c in claims:
            t[c[key]] = t.get(c[key], 0) + 1
        return t

    return {
        "schema": SCHEMA,
        "generated": as_of.isoformat(),
        "jurisdiction": JURISDICTION,
        "pilot": True,
        "canonicalModel": (
            "PlotNua evidence-manifest decomposition (authority, source_type, "
            "evidence_type, verification_method, verification_status, "
            "maturity, validity/staleness, provenance, homeowner_safe, "
            "logic_safe) plus claim_basis. evidence_state_derived is a DISPLAY "
            "LABEL computed from the dimensions above; it is never the stored "
            "truth and is never hand-set."
        ),
        "platformCount": 1,
        "platforms": [PLATFORM],
        "claimCount": len(claims),
        "claimsByBasis": tally("claim_basis"),
        "claimsByEvidenceType": tally("evidence_type"),
        "claimsBySourceType": tally("source_type"),
        "claimsByMaturity": tally("maturity"),
        "claimsByProvenance": tally("provenance"),
        "claimsByDerivedState": tally("evidence_state_derived"),
        "homeownerSafeCount": sum(1 for c in claims if c["homeowner_safe_resolved"]),
        "logicSafeCount": sum(1 for c in claims if c["logic_safe_resolved"]),
        "completionModel": COMPLETION_MODEL,
        "completion": {
            "status": "UNRESOLVED",
            "reason": (
                "Two decision-critical unknowns remain: the host fee rate "
                "(Commercial Terms) and the Republic of Ireland host "
                "protection position (Protection). A homeowner cannot work out "
                "what they would receive, or whether they are covered. Neither "
                "is a count failure — each is material to the next decision."
            ),
            "dimensionsEstablished": ["Identity", "Route", "Jurisdiction",
                                      "Exit", "Currency"],
            "dimensionsOpen": ["Commercial Terms", "Protection"],
            "note": (
                "Recorded as a judgement against completion_means, NOT as a "
                "5-of-7 score. An evidenced negative would satisfy a "
                "dimension; UNKNOWN does not."
            ),
        },
        "note": (
            "Generated by .github/scripts/generate_parking_platform_evidence.py. "
            "Do not hand-edit. Staleness is resolved at generation time. NOT "
            "homeowner-facing, NOT runtime-connected, NOT deployed. No Atlas "
            "Product record, Product Category or Product Type was created or "
            "modified for it."
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
        for field, allowed in (("claim_basis", CLAIM_BASIS),
                               ("evidence_type", EVIDENCE_TYPE),
                               ("source_type", SOURCE_TYPE),
                               ("provenance", PROVENANCE),
                               ("maturity", MATURITY)):
            if c[field] not in allowed:
                print(f"FAIL: {c['claim_key']}: bad {field}={c[field]!r}",
                      file=sys.stderr)
                return 1

    p = build(as_of)
    Path(a.out).write_text(json.dumps(p, indent=2, ensure_ascii=False) + "\n",
                           encoding="utf-8")
    print(f"  wrote {a.out}   schema {SCHEMA}")
    print(f"  platform  {ENTITY}")
    print(f"  claims    {p['claimCount']}")
    print(f"    basis            {p['claimsByBasis']}")
    print(f"    evidence_type    {p['claimsByEvidenceType']}")
    print(f"    derived state    {p['claimsByDerivedState']}")
    print(f"  homeowner-safe {p['homeownerSafeCount']}  logic-safe {p['logicSafeCount']}")
    print(f"  completion  {p['completion']['status']}  open: "
          f"{', '.join(p['completion']['dimensionsOpen'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
