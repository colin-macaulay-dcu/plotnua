#!/usr/bin/env python3
"""SOURCE OF RECORD — Driveway Income evidence substrate.

   Schema: plotnua.driveway.evidence.v1
   Emits:  driveway-evidence.json

   WHAT THIS FILE IS. The manifest the homeowner's browser will fetch is a
   GENERATED artefact. This script is the only place its content is written.
   driveway-evidence.json is never hand-edited; CI proves byte-identity.

   WHAT THIS FILE IS NOT. It is not research and it is not a fetcher. It
   contacts no authority, resolves no address, and computes nothing about a
   homeowner's property. Verification of the underlying facts is a human act
   with a review interval.

   THE ONE RULE THAT SHAPES EVERYTHING HERE. Gate 3 searched a large but
   BOUNDED set of Irish records and found no decision settling whether letting
   a driveway for payment remains incidental to the enjoyment of a house. That
   is an absence in PlotNua's search, not a gap in the authority's record. The
   two are not the same thing, and the difference is the whole reason the
   ABSENCE_OF_RECORD type exists:

     - permitted   : "we found no published Irish decision IN THE RECORDS
                      SEARCHED that settles this"
     - PROHIBITED  : "the Irish position has never been determined"

   An ABSENCE_OF_RECORD record therefore cannot exist without a search_scope
   that states what was searched and what was not, and it may never emit
   UNDETERMINED. The validator enforces both.

   STALENESS. Resolved at generation time, so no two clients can disagree
   about what is current. Absence records carry a SHORTER interval and a
   WITHHOLD policy: an absence that has not been re-searched is worth less
   than a published source that has not been re-read, because the world can
   fill an absence without anyone amending a document.
"""
import argparse
import hashlib
import json
import sys
from datetime import date, datetime

SCHEMA = "plotnua.driveway.evidence.v1"

RESULTS = ("PERMISSION", "TAX", "INSURANCE", "THE_DRIVEWAY")
EVIDENCE_TYPES = ("PUBLISHED_SOURCE", "ABSENCE_OF_RECORD", "JURISDICTION")
MONEY_LEVELS = ("NONE", "SCHEME_THRESHOLD")

FIELD_ORDER = [
    "evidence_id", "result", "claim_key", "claim", "value", "evidence_type",
    "jurisdiction", "authority", "source_title", "source_url", "source_type",
    "source_published_date", "valid_from", "valid_until", "last_verified",
    "review_interval_months", "verification_method", "maturity",
    "verification_status", "homeowner_safe", "logic_safe", "staleness_policy",
    "conflicts_with", "supersedes", "superseded_by", "search_scope",
    "money_level", "recheck_triggers", "prohibited_readings", "notes",
]

# ===========================================================================
# SEARCH SCOPES — the boundary an absence claim carries with it.
# Written once, referenced by id, so a scope cannot drift between records.
# ===========================================================================
PLANNING_SEARCH_SCOPE = {
    "searched_on": "2026-09-14",
    "question": ("Whether a householder letting their own driveway or domestic "
                 "parking space to a third party for payment remains incidental "
                 "to the enjoyment of the house as such."),
    "registers_searched": [
        {"register": "An Coimisiun Pleanala referral records",
         "coverage": "2016 to 2026-09-14",
         "filter": "case group RF (Referrals), types RL and RN",
         "method": "development-description search"},
        {"register": "An Coimisiun Pleanala archive",
         "coverage": "1995 to 2015",
         "filter": "groupCode RF",
         "method": "OData contains() on developmentDescription"},
        {"register": "Dun Laoghaire-Rathdown Section 5 declarations",
         "coverage": "2003-04-15 to 2026-09-09",
         "filter": "applicationType 'Section 5'",
         "method": "development-description search"},
        {"register": "Fingal Section 5 declarations",
         "coverage": "2002 to 2026",
         "filter": "applicationType 'Declaration under section 5'",
         "method": "development-description search"},
        {"register": "Dublin City exemption applications",
         "coverage": "1996 to 2026",
         "filter": "EXPP-prefixed exemption applications",
         "method": "development-description search"},
        {"register": "South Dublin Section 5 declarations",
         "coverage": "2008 to 2026",
         "filter": "applicationType 'Declaration of Exemption Section 5'",
         "method": "development-description search"},
    ],
    "terms": [
        "driveway", "parking", "paid parking", "pay parking", "parking space",
        "parking space rental", "parking space letting", "domestic parking",
        "residential parking", "public parking", "commercial parking",
        "car parking", "hardstanding", "hard surface", "forecourt",
        "curtilage", "incidental", "letting", "rental", "rent", "lease",
        "hire", "charge", "charging", "payment", "paid", "tenant", "commuter",
    ],
    "limitations": [
        "27 of Ireland's 31 planning authorities were not searched.",
        "Irish court judgments were not systematically searched.",
        "Dublin City single-token 'parking' query is capped server-side at "
        "20,300 records and returns HTTP 400; that term was reached only "
        "through adjacent terms.",
        "An Coimisiun Pleanala's 2016-onward interface truncates development "
        "descriptions at roughly 110 characters.",
        "Multi-word terms on the local-authority platform match as OR across "
        "tokens rather than as phrases: broad recall, weak precision.",
        "No inspector's report, planner's report or Board order was read. "
        "Outcomes are the published register decision strings only.",
    ],
    "conclusion_permitted": ("No published Irish decision was identified in the "
                            "records searched that settles this exact question."),
    "conclusion_prohibited": ("Any universal claim about the Irish record as "
                              "a whole. This search covered 4 of 31 planning "
                              "authorities and cannot speak for the rest."),
}

INSURANCE_SEARCH_SCOPE = {
    "searched_on": "2026-09-14",
    "question": ("Whether Irish regulatory or industry guidance specifically "
                 "addresses paid driveway parking at a home."),
    "registers_searched": [
        {"register": "gov.ie departmental guidance", "coverage": "current pages",
         "filter": None, "method": "targeted search"},
        {"register": "Citizens Information", "coverage": "current pages",
         "filter": None, "method": "targeted search"},
        {"register": "Revenue guidance", "coverage": "current pages",
         "filter": None, "method": "targeted search"},
    ],
    "terms": ["driveway", "parking", "paid parking", "insurance", "policy",
              "disclosure", "notify"],
    "limitations": [
        "Insurance Ireland and Central Bank of Ireland consumer materials were "
        "not systematically searched.",
        "Individual insurer policy wordings were not searched, and could not "
        "settle the question generally in any event.",
    ],
    "conclusion_permitted": ("No Irish guidance specifically addressing paid "
                            "driveway parking at a home was identified in the "
                            "sources searched."),
    "conclusion_prohibited": ("Any universal claim about insurer obligations, "
                              "about the continuing validity of a homeowner's "
                              "cover, or about whether the arrangement falls "
                              "within a policy."),
}

PLANNING_RECHECK = [
    "A new Exempted Development instrument is made.",
    "Any instrument amends S.I. No. 600 of 2001, Schedule 2, Part 1, Class 6.",
    "A relevant published Irish planning determination comes to light.",
]


def r(**kw):
    """One evidence record. Defaults are the conservative option in every case."""
    rec = {
        "evidence_id": kw["evidence_id"],
        "result": kw["result"],
        "claim_key": kw["claim_key"],
        "claim": kw["claim"],
        "value": kw.get("value"),
        "evidence_type": kw["evidence_type"],
        "jurisdiction": kw.get("jurisdiction", "IE-ROI"),
        "authority": kw["authority"],
        "source_title": kw.get("source_title"),
        "source_url": kw.get("source_url"),
        "source_type": kw["source_type"],
        "source_published_date": kw.get("source_published_date"),
        "valid_from": kw.get("valid_from"),
        "valid_until": kw.get("valid_until"),
        "last_verified": kw["last_verified"],
        "review_interval_months": kw["review_interval_months"],
        "verification_method": kw["verification_method"],
        "maturity": kw["maturity"],
        "homeowner_safe": kw.get("homeowner_safe", True),
        "logic_safe": kw.get("logic_safe", False),
        "staleness_policy": kw.get("staleness_policy", "DOWNGRADE"),
        "conflicts_with": kw.get("conflicts_with", []),
        "supersedes": kw.get("supersedes"),
        "superseded_by": kw.get("superseded_by"),
        "search_scope": kw.get("search_scope"),
        "money_level": kw.get("money_level", "NONE"),
        "recheck_triggers": kw.get("recheck_triggers", []),
        "prohibited_readings": kw.get("prohibited_readings", []),
        "notes": kw.get("notes"),
    }
    return rec


V = "2026-09-14"

RECORDS = [
    # =====================================================================
    # PERMISSION
    # =====================================================================
    r(evidence_id="permission-class6-current",
      result="PERMISSION",
      claim_key="planning_hardsurface_class_current",
      claim=("The exemption that covers a domestic driveway hard surface is "
             "Class 6 of Schedule 2, Part 1 to the Planning and Development "
             "Regulations 2001, as substituted in full by Article 6 of S.I. "
             "No. 454 of 2011."),
      value={"principal_instrument": "S.I. No. 600 of 2001",
             "location": "Schedule 2, Part 1, Class 6",
             "substituted_by": "S.I. No. 454 of 2011",
             "substituting_article": 6,
             "notice_published": "2011-09-13"},
      evidence_type="PUBLISHED_SOURCE",
      authority="Office of the Attorney General (Irish Statute Book)",
      source_title=("S.I. No. 454/2011 - Planning and Development (Amendment) "
                    "(No. 2) Regulations 2011"),
      source_url="https://www.irishstatutebook.ie/eli/2011/si/454/made/en/print",
      source_type="STATUTORY_INSTRUMENT",
      source_published_date="2011-09-13",
      valid_from="2011-09-13",
      last_verified=V, review_interval_months=12,
      verification_method="PRIMARY_FETCH",
      maturity="IN_FORCE",
      homeowner_safe=True, logic_safe=True,
      staleness_policy="DOWNGRADE",
      recheck_triggers=PLANNING_RECHECK,
      notes=("Gate 3C enumerated every Planning and Development Regulations "
             "instrument 2002-2026 from the Irish Statute Book year indexes and "
             "scanned each for 'Class 6' on a word boundary, 'hard surface' and "
             "'motor vehicles'. S.I. 454/2011 is the only instrument that "
             "substituted Part 1 Class 6. S.I. 649/2025 matches 'Class 6' but "
             "inserts Class 6A of PART 3 (agricultural slurry storage) and does "
             "not touch Part 1. The repealed vehicle-count condition has not "
             "been law since 13 September 2011."),
      prohibited_readings=[
          "Any statement of the pre-2011 vehicle-count condition as current law.",
      ]),

    r(evidence_id="permission-incidental-test",
      result="PERMISSION",
      claim_key="planning_incidental_test_wording",
      claim=("Current Class 6(b)(ii) exempts the provision of a hard surface in "
             "the area of the garden forward of the front building line of the "
             "house, or to the side of the side building line, for purposes "
             "incidental to the enjoyment of the house as such. Where that hard "
             "surface is 25 square metres or greater, or comprises more than 50 "
             "per cent of that part of the garden, whichever is the smaller, it "
             "must be constructed using permeable materials or otherwise allow "
             "rainwater to soak into the ground."),
      value={"test": "incidental to the enjoyment of the house as such",
             "locations": ["forward of the front building line",
                           "to the side of the side building line"],
             "area_threshold_sqm": 25,
             "garden_share_threshold_pct": 50,
             "threshold_rule": "whichever is the smaller",
             "condition_above_threshold": ("permeable materials, or otherwise "
                                           "allow rainwater to soak into the "
                                           "ground"),
             "vehicle_count_limit": None},
      evidence_type="PUBLISHED_SOURCE",
      authority="Office of the Attorney General (Irish Statute Book)",
      source_title=("S.I. No. 454/2011, Article 6 - substitution of Class 6 of "
                    "Schedule 2, Part 1"),
      source_url="https://www.irishstatutebook.ie/eli/2011/si/454/made/en/print",
      source_type="STATUTORY_INSTRUMENT",
      source_published_date="2011-09-13",
      valid_from="2011-09-13",
      last_verified=V, review_interval_months=12,
      verification_method="PRIMARY_FETCH",
      maturity="IN_FORCE",
      homeowner_safe=True, logic_safe=True,
      staleness_policy="DOWNGRADE",
      recheck_triggers=PLANNING_RECHECK,
      notes=("vehicle_count_limit is null because the substituted Class 6 "
             "contains no vehicle count, NOT because vehicle numbers are "
             "unconstrained. The incidental test survives, and conditions "
             "attached to an individual property can still bite."),
      prohibited_readings=[
          "Reading a null vehicle_count_limit as an absence of any constraint "
          "on how many vehicles may use a driveway.",
      ]),

    r(evidence_id="permission-no-exact-decision",
      result="PERMISSION",
      claim_key="planning_no_exact_decision_located",
      claim=("No published Irish planning decision settling whether letting a "
             "driveway or domestic parking space for payment remains incidental "
             "to the enjoyment of the house was identified in the records "
             "searched."),
      value=None,
      evidence_type="ABSENCE_OF_RECORD",
      authority="PlotNua evidence search",
      source_title="PlotNua Gate 3B/3C planning evidence search",
      source_url=None,
      source_type="EVIDENCE_SEARCH",
      source_published_date=None,
      last_verified=V, review_interval_months=6,
      verification_method="REGISTER_SEARCH",
      maturity="BOUNDED_SEARCH",
      homeowner_safe=True, logic_safe=True,
      staleness_policy="WITHHOLD",
      search_scope=PLANNING_SEARCH_SCOPE,
      recheck_triggers=PLANNING_RECHECK,
      notes=("This record states the result of a search, not the state of the "
             "law. 27 of 31 planning authorities are unsearched, and related "
             "determinations were in fact found, so the record must always be "
             "presented alongside planning_related_decisions_exist."),
      prohibited_readings=[
          "Any universal statement that the question has not been settled "
          "anywhere in Ireland.",
          "Emission of an authority-gap result state on the strength of this "
          "record.",
          "Presentation of this record without planning_related_decisions_exist.",
      ]),

    r(evidence_id="permission-related-decisions",
      result="PERMISSION",
      claim_key="planning_related_decisions_exist",
      claim=("Irish planning authorities and An Coimisiun Pleanala have "
             "determined related questions, including the use of a residential "
             "garden for commercial parking, the use of permitted parking "
             "spaces for public parking, and the parking of work vehicles at a "
             "home. None of them answers the driveway-letting question."),
      value={"categories": ["commercial parking in a residential garden",
                            "public parking at permitted spaces",
                            "work vehicles parked at a home"]},
      evidence_type="PUBLISHED_SOURCE",
      authority="Irish planning authorities and An Coimisiun Pleanala",
      source_title="Section 5 / exemption registers and ABP referral records",
      source_url="https://www.pleanala.ie/en-ie/case-search",
      source_type="PLANNING_REGISTER",
      source_published_date=None,
      last_verified=V, review_interval_months=6,
      verification_method="REGISTER_SEARCH",
      maturity="BOUNDED_SEARCH",
      homeowner_safe=True, logic_safe=True,
      staleness_policy="DOWNGRADE",
      search_scope=PLANNING_SEARCH_SCOPE,
      recheck_triggers=PLANNING_RECHECK,
      notes=("Representative records, held here and NOT in homeowner copy: "
             "DCC 0324/05 (use of garden as commercial parking, Merrion Road) "
             "decided 'Not Exemption' 2005-07-15; ABP 307078 and Fingal "
             "FS5/048/19 (school bus parked at a house) both not exempted; ABP "
             "317272 / DLR REF3923 (introduction of pay car parking); ABP "
             "300501 (permitted spaces used for public parking). Outcomes are "
             "register decision strings; no reasoning was read, so no ratio may "
             "be attributed to any of them.")),

    r(evidence_id="permission-section5-route",
      result="PERMISSION",
      claim_key="planning_section5_route",
      claim=("Any person may request a declaration from the planning authority "
             "under section 5 of the Planning and Development Act 2000 as to "
             "whether a development is or is not exempted development. That is "
             "the route to certainty for a particular address."),
      value={"act": "Planning and Development Act 2000", "section": 5,
             "decided_by": "the planning authority for the address",
             "appealable_to": "An Coimisiun Pleanala"},
      evidence_type="PUBLISHED_SOURCE",
      authority="Office of the Attorney General (Irish Statute Book)",
      source_title="Planning and Development Act 2000, section 5",
      source_url="https://www.irishstatutebook.ie/eli/2000/act/30/section/5/enacted/en/html",
      source_type="PRIMARY_LEGISLATION",
      source_published_date=None,
      last_verified=V, review_interval_months=12,
      verification_method="PRIMARY_FETCH",
      maturity="IN_FORCE",
      homeowner_safe=True, logic_safe=True,
      staleness_policy="DOWNGRADE",
      recheck_triggers=PLANNING_RECHECK,
      notes=("No fee and no statutory period is carried in V1. Fees are "
             "prescribed by regulation and were confirmed for two authorities "
             "only; a national figure was not verified, so none is stated.")),

    r(evidence_id="permission-england-not-applicable",
      result="PERMISSION",
      claim_key="planning_england_guidance_not_applicable",
      claim=("English planning guidance on letting a parking space has no "
             "application in Ireland."),
      value={"excluded_jurisdiction": "GB-ENG", "applies_in": "IE-ROI"},
      evidence_type="JURISDICTION",
      authority="PlotNua jurisdictional governance",
      source_title=None, source_url=None,
      source_type="JURISDICTION_RULE",
      source_published_date=None,
      last_verified=V, review_interval_months=24,
      verification_method="EDITORIAL_GOVERNANCE",
      maturity="STANDING_RULE",
      homeowner_safe=True, logic_safe=True,
      staleness_policy="DOWNGRADE",
      notes=("Ireland and England have separate planning codes. English "
             "guidance is frequently surfaced to Irish homeowners by search "
             "engines, which is why this is carried as evidence rather than "
             "left implicit.")),

    # =====================================================================
    # TAX
    # =====================================================================
    r(evidence_id="tax-driveway-income-taxable",
      result="TAX",
      claim_key="driveway_income_is_taxable",
      claim=("Income from letting a parking space is taxable and must be "
             "declared."),
      value=None,
      evidence_type="PUBLISHED_SOURCE",
      authority="Revenue Commissioners",
      source_title="Irish rental income",
      source_url="https://www.revenue.ie/en/property/rental-income/irish-rental-income/index.aspx",
      source_type="AUTHORITY_GUIDANCE",
      source_published_date=None,
      last_verified=V, review_interval_months=12,
      verification_method="PRIMARY_FETCH",
      maturity="CURRENT_GUIDANCE",
      homeowner_safe=True, logic_safe=True,
      staleness_policy="DOWNGRADE",
      notes=("No filing route, form number or self-assessment threshold is "
             "carried in V1."),
      prohibited_readings=[
          "Any non-PAYE self-assessment threshold figure.",
          "Any filing-form route.",
      ]),

    r(evidence_id="tax-rar-scope",
      result="TAX",
      claim_key="rent_a_room_scope_residential_rooms",
      claim=("Rent-a-Room Relief applies to income received for the use of a "
             "room or rooms in a qualifying residence, let as residential "
             "accommodation."),
      value={"scope": "a room or rooms in a qualifying residence",
             "use": "residential accommodation",
             "minimum_letting_days": 28},
      evidence_type="PUBLISHED_SOURCE",
      authority="Revenue Commissioners",
      source_title="Rent-a-Room Relief - What conditions must be met?",
      source_url="https://www.revenue.ie/en/personal-tax-credits-reliefs-and-exemptions/land-and-property/rent-a-room-relief/qualifying-conditions.aspx",
      source_type="AUTHORITY_GUIDANCE",
      source_published_date="2026-01-08",
      last_verified=V, review_interval_months=12,
      verification_method="PRIMARY_FETCH",
      maturity="CURRENT_GUIDANCE",
      homeowner_safe=True, logic_safe=True,
      staleness_policy="DOWNGRADE",
      notes=("PlotNua states Revenue's SCOPE and lets the scope carry the "
             "conclusion. Revenue has not published a sentence saying the "
             "relief does not apply to a parking space, and PlotNua does not "
             "attribute one to them. A parking space is not a room and is not "
             "residential accommodation; that is why the relief does not reach "
             "driveway income.")),

    r(evidence_id="tax-rar-limit",
      result="TAX",
      claim_key="rent_a_room_limit_eur",
      claim=("The annual Rent-a-Room Relief exemption limit is EUR 14,000, "
             "applied to gross income before expenses. If gross income exceeds "
             "the limit, the total amount is taxed."),
      value={"amount": 14000, "currency": "EUR", "basis": "GROSS_ANNUAL",
             "expenses_deductible_before_test": False,
             "all_or_nothing": True},
      evidence_type="PUBLISHED_SOURCE",
      authority="Revenue Commissioners",
      source_title="Rent-a-Room Relief - What conditions must be met?",
      source_url="https://www.revenue.ie/en/personal-tax-credits-reliefs-and-exemptions/land-and-property/rent-a-room-relief/qualifying-conditions.aspx",
      source_type="AUTHORITY_GUIDANCE",
      source_published_date="2026-01-08",
      last_verified=V, review_interval_months=12,
      verification_method="PRIMARY_FETCH",
      maturity="CURRENT_GUIDANCE",
      homeowner_safe=True, logic_safe=True,
      staleness_policy="DOWNGRADE",
      money_level="SCHEME_THRESHOLD",
      notes=("Carried so PlotNua can correct the common belief that this "
             "allowance covers driveway income. It is a published statutory "
             "scheme threshold, not an earnings figure, and it is never applied "
             "to a homeowner's own numbers.")),

    r(evidence_id="tax-rar-prsi-usc",
      result="TAX",
      claim_key="rent_a_room_exempt_from_prsi_usc",
      claim=("Where gross rental income does not exceed the Rent-a-Room "
             "exemption limit, it is not liable to Income Tax, PRSI or USC."),
      value={"exempt_from": ["INCOME_TAX", "PRSI", "USC"],
             "condition": "gross income at or below the exemption limit"},
      evidence_type="PUBLISHED_SOURCE",
      authority="Revenue Commissioners",
      source_title="Rent-a-Room Relief - What conditions must be met?",
      source_url="https://www.revenue.ie/en/personal-tax-credits-reliefs-and-exemptions/land-and-property/rent-a-room-relief/qualifying-conditions.aspx",
      source_type="AUTHORITY_GUIDANCE",
      source_published_date="2026-01-08",
      last_verified=V, review_interval_months=12,
      verification_method="PRIMARY_FETCH",
      maturity="CURRENT_GUIDANCE",
      homeowner_safe=True, logic_safe=True,
      staleness_policy="DOWNGRADE",
      notes=("Held to make the contrast exact: the relief a homeowner is "
             "thinking of is genuinely generous, and genuinely does not reach "
             "a driveway.")),

    # =====================================================================
    # INSURANCE
    # =====================================================================
    r(evidence_id="insurance-precontract-duty",
      result="INSURANCE",
      claim_key="insurance_precontract_duty_scope",
      claim=("Under the Consumer Insurance Contracts Act 2019 a consumer's "
             "pre-contractual duty of disclosure is confined to providing "
             "responses to the questions the insurer asks, answered honestly "
             "and with reasonable care. The consumer is under no duty to "
             "volunteer information beyond those questions."),
      value={"act": "Consumer Insurance Contracts Act 2019",
             "act_number": 53, "act_year": 2019,
             "sections": ["8(1)", "8(2)", "8(7)(a)"],
             "replaces": "uberrima fides at the pre-contractual stage"},
      evidence_type="PUBLISHED_SOURCE",
      authority="Office of the Attorney General (Irish Statute Book)",
      source_title="Consumer Insurance Contracts Act 2019, section 8",
      source_url="https://www.irishstatutebook.ie/eli/2019/act/53/enacted/en/print",
      source_type="PRIMARY_LEGISLATION",
      source_published_date=None,
      last_verified=V, review_interval_months=12,
      verification_method="PRIMARY_FETCH",
      maturity="IN_FORCE",
      homeowner_safe=True, logic_safe=True,
      staleness_policy="DOWNGRADE",
      notes=("States the PRE-CONTRACTUAL position only. It does not say a "
             "homeowner need tell their insurer nothing, and it must never be "
             "presented that way. Section 15 governs the position during the "
             "contract and is carried separately.")),

    r(evidence_id="insurance-proportionate-remedies",
      result="INSURANCE",
      claim_key="insurance_misrepresentation_remedies_proportionate",
      claim=("Where a consumer has answered the insurer's questions honestly "
             "and with reasonable care, an innocent misrepresentation does not "
             "entitle the insurer to avoid the contract and the claim must be "
             "paid. A negligent misrepresentation attracts a compensatory and "
             "proportionate remedy."),
      value={"act": "Consumer Insurance Contracts Act 2019",
             "sections": ["9(1)", "9(2)", "9(3)"],
             "innocent": "insurer must pay; cannot avoid",
             "negligent": "compensatory and proportionate remedy"},
      evidence_type="PUBLISHED_SOURCE",
      authority="Office of the Attorney General (Irish Statute Book)",
      source_title="Consumer Insurance Contracts Act 2019, section 9",
      source_url="https://www.irishstatutebook.ie/eli/2019/act/53/enacted/en/print",
      source_type="PRIMARY_LEGISLATION",
      source_published_date=None,
      last_verified=V, review_interval_months=12,
      verification_method="PRIMARY_FETCH",
      maturity="IN_FORCE",
      homeowner_safe=False, logic_safe=True,
      staleness_policy="DOWNGRADE",
      notes=("homeowner_safe is FALSE on purpose. The remedy ladder is "
             "accurate and useful to PlotNua's reasoning, but presenting it to "
             "a homeowner invites them to work out how wrong an answer they "
             "could give and still be paid. It informs what PlotNua will not "
             "say; it is not itself said."),
      prohibited_readings=[
          "Presentation to a homeowner in any form.",
          "Any suggestion that an inaccurate answer to an insurer carries no "
          "consequence.",
      ]),

    r(evidence_id="insurance-alteration-of-risk",
      result="INSURANCE",
      claim_key="insurance_alteration_of_risk_limits",
      claim=("An alteration of risk clause applies only where the subject "
             "matter of the contract of insurance has altered, and is void "
             "where it purports to apply to a modification only of the risk "
             "insured."),
      value={"act": "Consumer Insurance Contracts Act 2019",
             "sections": ["15(3)", "15(4)"],
             "applies_only_if": "the subject matter of the contract has altered",
             "void_if": "it purports to apply to a modification only of the risk"},
      evidence_type="PUBLISHED_SOURCE",
      authority="Office of the Attorney General (Irish Statute Book)",
      source_title="Consumer Insurance Contracts Act 2019, section 15",
      source_url="https://www.irishstatutebook.ie/eli/2019/act/53/enacted/en/print",
      source_type="PRIMARY_LEGISLATION",
      source_published_date=None,
      last_verified=V, review_interval_months=12,
      verification_method="PRIMARY_FETCH",
      maturity="IN_FORCE",
      homeowner_safe=False, logic_safe=True,
      staleness_policy="DOWNGRADE",
      notes=("Whether a particular arrangement alters the subject matter of a "
             "particular policy is a question about that policy, which only "
             "the insurer can answer."),
      prohibited_readings=[
          "Any statement that a driveway arrangement has this effect on a "
          "homeowner's own policy.",
          "Any assertion about the continuing validity of a homeowner's cover.",
      ]),

    r(evidence_id="insurance-no-irish-guidance",
      result="INSURANCE",
      claim_key="insurance_no_irish_guidance_located",
      claim=("No Irish guidance specifically addressing paid driveway parking "
             "at a home was identified in the sources searched."),
      value=None,
      evidence_type="ABSENCE_OF_RECORD",
      authority="PlotNua evidence search",
      source_title="PlotNua Gate 3/3B insurance guidance search",
      source_url=None,
      source_type="EVIDENCE_SEARCH",
      source_published_date=None,
      last_verified=V, review_interval_months=6,
      verification_method="TARGETED_SEARCH",
      maturity="BOUNDED_SEARCH",
      homeowner_safe=True, logic_safe=True,
      staleness_policy="WITHHOLD",
      search_scope=INSURANCE_SEARCH_SCOPE,
      notes=("Supports the homeowner action 'Check with your insurer before "
             "anyone parks.'"),
      prohibited_readings=[
          "Any general obligation on a homeowner to contact an insurer "
          "unprompted.",
          "Any statement about the continuing validity of a homeowner's cover.",
          "Any statement that the arrangement does or does not fall within a "
          "policy.",
      ]),
]


# ===========================================================================
# STALENESS RESOLUTION — first match wins. Resolved here, at generation time,
# so no two clients can disagree about what is current.
# ===========================================================================
def months_between(a: date, b: date) -> int:
    return (b.year - a.year) * 12 + (b.month - a.month) - (1 if b.day < a.day else 0)


def resolve(rec, as_of: date):
    def d(field):
        return datetime.strptime(rec[field], "%Y-%m-%d").date() if rec.get(field) else None

    if rec.get("superseded_by"):
        return "SUPERSEDED", "superseded_by is set"
    if rec.get("conflicts_with"):
        return "WITHHOLD", "conflicts with another authoritative record"

    vf = d("valid_from")
    if rec["maturity"] == "ANNOUNCED_FUTURE_CHANGE" and (vf is None or vf > as_of):
        return "NOT_YET_IN_FORCE", "announced, not yet in force"

    vu = d("valid_until")
    if vu and vu < as_of:
        if rec["staleness_policy"] in ("SAFE_UNTIL_EXPIRY", "WITHHOLD"):
            return "WITHHOLD", f"expired on {rec['valid_until']}"
        return "RECHECK_REQUIRED", f"expired on {rec['valid_until']}"

    lv = d("last_verified")
    if lv and months_between(lv, as_of) >= rec["review_interval_months"]:
        #  An absence that has not been re-searched is WITHHELD, never
        #  downgraded and never silently left CURRENT. The world can fill an
        #  absence without anyone amending a document.
        if rec["staleness_policy"] == "WITHHOLD":
            return "WITHHOLD", "search interval elapsed; absence not re-verified"
        return "RECHECK_REQUIRED", "verification interval elapsed"

    return "CURRENT", None


def build(as_of: date):
    out = []
    for rec in RECORDS:
        rec = dict(rec)
        status, why = resolve(rec, as_of)
        rec["verification_status"] = status
        rec["verification_reason"] = why
        # A record that is not CURRENT can never be served as current evidence,
        # whatever its own flags say. Enforced here so the client cannot differ.
        if status != "CURRENT":
            rec["homeowner_safe_resolved"] = False
            rec["logic_safe_resolved"] = False
        else:
            rec["homeowner_safe_resolved"] = rec["homeowner_safe"]
            rec["logic_safe_resolved"] = rec["logic_safe"]
        out.append({k: rec[k] for k in FIELD_ORDER if k in rec} |
                   {"verification_reason": rec["verification_reason"],
                    "homeowner_safe_resolved": rec["homeowner_safe_resolved"],
                    "logic_safe_resolved": rec["logic_safe_resolved"]})
    by_result = {}
    for rec in out:
        by_result[rec["result"]] = by_result.get(rec["result"], 0) + 1
    return {
        "schema": SCHEMA,
        "generated": as_of.isoformat(),
        "jurisdiction": "IE-ROI",
        "results": list(RESULTS),
        "recordCount": len(out),
        "recordsByResult": {k: by_result.get(k, 0) for k in RESULTS},
        "note": ("Generated by .github/scripts/generate_driveway_evidence.py. "
                 "Do not hand-edit. Staleness is resolved at generation time so "
                 "no two clients can disagree about what is current. "
                 "THE_DRIVEWAY carries no evidence records by design: it is "
                 "answered from the homeowner's own answers, never from a "
                 "source, an inference or a location."),
        "records": out,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None)
    ap.add_argument("--as-of", default=None,
                    help="Generate for this date (YYYY-MM-DD) instead of today.")
    a = ap.parse_args()
    as_of = (datetime.strptime(a.as_of, "%Y-%m-%d").date() if a.as_of
             else date.today())
    doc = build(as_of)
    text = json.dumps(doc, indent=2, ensure_ascii=True) + "\n"
    if a.out:
        with open(a.out, "w", encoding="utf-8") as fh:
            fh.write(text)
        print(f"wrote {a.out}")
        print(f"  records : {doc['recordCount']}")
        print(f"  by result: {doc['recordsByResult']}")
        print(f"  sha256  : {hashlib.sha256(text.encode()).hexdigest()}")
    else:
        sys.stdout.write(text)


if __name__ == "__main__":
    main()
