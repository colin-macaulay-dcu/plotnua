#!/usr/bin/env python3
"""
PlotNua — DISC-026 evidence manifest GENERATOR.

    generate_disc026_evidence.py [--out FILE] [--as-of YYYY-MM-DD]

Emits `disc026-evidence.json`: the evidence substrate the V1 House as a Power
Station journey consumes. Gate 4 model, Gate 5 claim_key contract.

WHY A GENERATOR AND NOT A HAND-EDITED FILE.

  The architecture (§12) requires that staleness is resolved BEFORE or DURING
  generation, never in the browser. If the client computed it, two devices in
  two timezones could disagree about whether the 2026 grant maximum is still
  current. So `resolved_status` is computed here, once, and shipped.

  This file is the source of record. The JSON is an artefact. Edit the records
  below; never hand-edit the JSON.

THE SEPARATION THIS EXISTS TO ENFORCE (architecture §11.1):

    EVIDENCE FACT  !=  ENGINE LOGIC  !=  PRESENTATION

  Every record states WHAT IS TRUE and how current it is. Not one contains a
  conditional, a recommendation, or anything about a particular homeowner.
  The journey binds to `claim_key`, never to `claim` prose — so a copy edit
  here can never change behaviour there.

--as-of exists so the temporal model can be PROVEN rather than asserted. Run it
at 2027-01-01 and the 2026 grant maximum must stop being CURRENT without one
line of business logic changing.

Verification date for every record: 14 September 2026 (Gate 4), with the MAKE
block re-read against SEAI on the same date before encoding.
"""
import argparse
import json
import sys
from datetime import date, datetime
from pathlib import Path

SCHEMA = "plotnua.disc026.evidence.v1"

# Default re-verification windows by source type, in months. A statutory
# instrument and a grant scheme page do not decay at the same speed: scheme
# values move with budgets, statute does not.
DEFAULT_REVIEW = {
    "STATUTE_SI": 24,
    "REGULATOR_DECISION": 12,
    "OPERATOR_STANDARD": 12,
    "TAX_RULE": 12,
    "SCHEME_PAGE": 6,
    "PRESS_RELEASE": 6,
    "SECONDARY": 3,
}

SEAI_SOLAR = "https://www.seai.ie/grants/home-energy-grants/individual-grants/solar-electricity-grant"
SEAI_HOME = "https://www.seai.ie/grants/home-energy-grants"
CI_SOLAR = "https://www.citizensinformation.ie/en/housing/housing-grants-and-schemes/grants-for-home-renovations-and-improvements/grants-for-solar-panels/"
CI_MICRO = "https://www.citizensinformation.ie/en/environment/environmental-grants-and-schemes-for-your-home/micro-generation/"
GOV_SOLAR = "https://www.gov.ie/en/department-of-housing-local-government-and-heritage/publications/solar-planning-exemptions/"
CRU_QA = "https://cruie-live-96ca64acab2247eca8a850a7e54b-5b34f62.divio-media.com/documents/CRU202366_CRU_Microgeneration_QAs__-_V1.0_Updated.pdf"
ESB_SMART = "https://esb.ie/news---insights/press-releases/article/2025/09/04/over-two-million-smart-meters-installed-nationwide-as-part-of-the-national-smart-metering-programme"
ESBN_BESS = "https://media.esbnetworks.ie/media/docs/default-source/publications/quick-user-guide-microgeneration-and-smart-battery-energy-storage.pdf?sfvrsn=67d5102a_0"
ESBN_COND = "https://www.esbnetworks.ie/docs/default-source/publications/conditions-governing-the-connection-and-operation-of-micro-generation-policy.pdf"

V = "2026-09-14"          # last_verified for every record in this generation


def r(**kw):
    """One evidence record. Defaults are the conservative choice in each case."""
    rec = {
        "evidence_id": kw["evidence_id"],
        "opportunity": kw["opportunity"],
        "claim_key": kw["claim_key"],
        "claim": kw["claim"],
        "value": kw.get("value"),
        "jurisdiction": kw.get("jurisdiction", "IE-ROI"),
        "authority": kw["authority"],
        "source_title": kw["source_title"],
        "source_url": kw["source_url"],
        "source_type": kw["source_type"],
        "source_published_date": kw.get("source_published_date"),
        "valid_from": kw.get("valid_from"),
        "valid_until": kw.get("valid_until"),
        "last_verified": kw.get("last_verified", V),
        "review_interval_months": kw.get(
            "review_interval_months", DEFAULT_REVIEW[kw["source_type"]]),
        "verification_method": kw.get("verification_method", "PRIMARY_FETCH"),
        "maturity": kw["maturity"],
        "homeowner_safe": kw["homeowner_safe"],
        "logic_safe": kw["logic_safe"],
        "staleness_policy": kw.get("staleness_policy", "DOWNGRADE"),
        "supersedes": kw.get("supersedes"),
        "superseded_by": kw.get("superseded_by"),
        "conflicts_with": kw.get("conflicts_with", []),
        "notes": kw.get("notes"),
        "source_reachable": kw.get("source_reachable", True),
    }
    return rec


# ===========================================================================
# MAKE — solar generation
# ===========================================================================
RECORDS = [
    r(evidence_id="make-grant-structure", opportunity="MAKE",
      claim_key="grant_structure",
      claim="The domestic Solar PV grant is EUR 700 per kWp up to 2 kWp, then "
            "EUR 200 for every additional kWp up to 4 kWp, paid pro rata.",
      value={"per_kwp_first": 700, "per_kwp_additional": 200,
             "first_band_kwp": 2, "max_band_kwp": 4, "currency": "EUR",
             "pro_rata": True},
      authority="SEAI", source_title="Solar electricity grant (solar PV)",
      source_url=SEAI_SOLAR, source_type="SCHEME_PAGE",
      maturity="CURRENT_SCHEME", homeowner_safe=True, logic_safe=True),

    r(evidence_id="make-grant-max-2026", opportunity="MAKE",
      claim_key="grant_max_eur",
      claim="The maximum domestic Solar PV grant is EUR 1,800 in 2026.",
      value={"amount": 1800, "currency": "EUR", "year": 2026},
      authority="SEAI", source_title="Solar electricity grant (solar PV)",
      source_url=SEAI_SOLAR, source_type="SCHEME_PAGE",
      valid_from="2026-01-01", valid_until="2026-12-31",
      maturity="CURRENT_SCHEME", staleness_policy="SAFE_UNTIL_EXPIRY",
      homeowner_safe=True, logic_safe=True,
      notes="Stated per calendar year. Withholds itself on 2027-01-01 with no "
            "code change. A 2027 value must be VERIFIED, never inferred."),

    r(evidence_id="make-grant-reduction-announced", opportunity="MAKE",
      claim_key="grant_reduction_announced",
      claim="The Government plans to reduce the grant by up to EUR 300 each "
            "year as panel costs fall.",
      value=None, authority="CITIZENS_INFO",
      source_title="Grants for solar panels", source_url=CI_SOLAR,
      source_type="SECONDARY", source_published_date="2026-03-10",
      maturity="ANNOUNCED_FUTURE_CHANGE",
      homeowner_safe=True, logic_safe=False,
      notes="ANNOUNCED, not in force. Must never be applied as a current "
            "value. Context only."),

    r(evidence_id="make-grant-end-2029", opportunity="MAKE",
      claim_key="grant_scheme_end_announced",
      claim="The grant is due to end in 2029.",
      value={"year": 2029}, authority="CITIZENS_INFO",
      source_title="Grants for solar panels", source_url=CI_SOLAR,
      source_type="SECONDARY", source_published_date="2026-03-10",
      maturity="ANNOUNCED_FUTURE_CHANGE",
      homeowner_safe=True, logic_safe=False,
      notes="ANNOUNCED. Not an expiry on any current record."),

    r(evidence_id="make-eligibility-pre2021", opportunity="MAKE",
      claim_key="grant_requires_pre_2021",
      claim="The home must have been built and occupied before 2021.",
      value={"before_year": 2021}, authority="SEAI",
      source_title="Solar electricity grant (solar PV)", source_url=SEAI_SOLAR,
      source_type="SCHEME_PAGE", maturity="CURRENT_SCHEME",
      homeowner_safe=True, logic_safe=True),

    r(evidence_id="make-one-per-mprn", opportunity="MAKE",
      claim_key="grant_once_per_mprn",
      claim="The grant is not open to homes with previous funding for solar PV "
            "at that MPRN, whoever claimed it.",
      value={"once_per_mprn": True}, authority="SEAI",
      source_title="Solar electricity grant (solar PV)", source_url=SEAI_SOLAR,
      source_type="SCHEME_PAGE", maturity="CURRENT_SCHEME",
      homeowner_safe=True, logic_safe=True,
      notes="Applies across ownership changes. A previous owner's claim uses it."),

    r(evidence_id="make-mprn-required", opportunity="MAKE",
      claim_key="grant_requires_mprn",
      claim="The home needs an MPRN.",
      value={"mprn_required": True}, authority="SEAI",
      source_title="Solar electricity grant (solar PV)", source_url=SEAI_SOLAR,
      source_type="SCHEME_PAGE", maturity="CURRENT_SCHEME",
      homeowner_safe=True, logic_safe=True),

    r(evidence_id="make-eligible-owners", opportunity="MAKE",
      claim_key="grant_eligible_applicants",
      claim="Eligible applicants are all homeowners including private "
            "landlords, owner management companies, and approved housing bodies.",
      value={"applicants": ["homeowner", "private_landlord",
                            "owner_management_company", "approved_housing_body"]},
      authority="SEAI", source_title="Solar electricity grant (solar PV)",
      source_url=SEAI_SOLAR, source_type="SCHEME_PAGE",
      maturity="CURRENT_SCHEME", homeowner_safe=True, logic_safe=True),

    r(evidence_id="make-8-month-window", opportunity="MAKE",
      claim_key="grant_completion_window_months",
      claim="Once approved there are 8 months to complete the works and submit "
            "the documentation, after which the grant expires.",
      value={"months": 8}, authority="SEAI",
      source_title="Solar electricity grant (solar PV)", source_url=SEAI_SOLAR,
      source_type="SCHEME_PAGE", maturity="CURRENT_SCHEME",
      homeowner_safe=True, logic_safe=False),

    r(evidence_id="make-nc6-before-install", opportunity="MAKE",
      claim_key="grant_nc6_lead_time",
      claim="The installer applies to ESB Networks before the system is "
            "installed; the application usually takes at least 4 weeks.",
      value={"working_days_min": 20}, authority="SEAI",
      source_title="Solar electricity grant (solar PV)", source_url=SEAI_SOLAR,
      source_type="SCHEME_PAGE", maturity="CURRENT_REGULATORY_REQUIREMENT",
      homeowner_safe=True, logic_safe=False),

    r(evidence_id="make-post-works-ber", opportunity="MAKE",
      claim_key="grant_requires_post_works_ber",
      claim="A post-works BER assessment is required before the grant is paid.",
      value={"required": True}, authority="SEAI",
      source_title="Solar electricity grant (solar PV)", source_url=SEAI_SOLAR,
      source_type="SCHEME_PAGE", maturity="CURRENT_SCHEME",
      homeowner_safe=True, logic_safe=False),

    r(evidence_id="make-payment-timing", opportunity="MAKE",
      claim_key="grant_payment_timing",
      claim="Allow 4 to 6 weeks for the grant payment once the documents and "
            "the published BER are in.",
      value={"weeks_min": 4, "weeks_max": 6}, authority="SEAI",
      source_title="Solar electricity grant (solar PV)", source_url=SEAI_SOLAR,
      source_type="SCHEME_PAGE", maturity="CURRENT_SCHEME",
      homeowner_safe=True, logic_safe=False),

    r(evidence_id="make-vat-zero", opportunity="MAKE",
      claim_key="solar_vat_rate",
      claim="A 0% VAT rate applies to the supply and installation of solar "
            "panels on private dwellings.",
      value={"rate_percent": 0}, authority="CITIZENS_INFO",
      source_title="Grants for solar panels", source_url=CI_SOLAR,
      source_type="SECONDARY", source_published_date="2026-03-10",
      valid_from="2023-05-01", maturity="CURRENT_RULE",
      homeowner_safe=True, logic_safe=False),

    r(evidence_id="make-planning-exempt-houses", opportunity="MAKE",
      claim_key="planning_exempt_houses",
      claim="Rooftop solar panels on houses do not require planning permission.",
      value={"exempt": True}, authority="GOV_IE",
      source_title="Solar Planning Exemptions (S.I. 493 of 2022)",
      source_url=GOV_SOLAR, source_type="STATUTE_SI",
      source_published_date="2022-10-07", valid_from="2022-10-05",
      maturity="CURRENT_RULE", homeowner_safe=True, logic_safe=True),

    r(evidence_id="make-no-area-limit-houses", opportunity="MAKE",
      claim_key="planning_no_area_limit_houses",
      claim="There is no rooftop area limit on houses, whether or not the house "
            "is inside a Solar Safeguarding Zone.",
      value={"area_limit_m2": None}, authority="GOV_IE",
      source_title="Solar Planning Exemptions (S.I. 492 and 493 of 2022)",
      source_url=GOV_SOLAR, source_type="STATUTE_SI",
      source_published_date="2022-10-07", valid_from="2022-10-05",
      maturity="CURRENT_RULE", homeowner_safe=True, logic_safe=True,
      notes="Solar Safeguarding Zones apply to every building class EXCEPT "
            "houses. A prior PlotNua reading of this was wrong and was "
            "corrected on the live Discovery on 14 September 2026."),

    r(evidence_id="make-protected-structure-aca", opportunity="MAKE",
      claim_key="planning_protected_structure_aca",
      claim="Restrictions still apply to protected structures and homes in an "
            "Architectural Conservation Area, and the exemption carries "
            "conditions such as a minimum distance from the edge of the roof.",
      value=None, authority="GOV_IE",
      source_title="Solar Planning Exemptions",
      source_url=GOV_SOLAR, source_type="STATUTE_SI",
      source_published_date="2022-10-07", maturity="CURRENT_RULE",
      homeowner_safe=True, logic_safe=False),

    r(evidence_id="make-seai-no-warranty", opportunity="MAKE",
      claim_key="seai_does_not_warranty_contractor",
      claim="SEAI does not approve, guarantee, or warranty a company or their "
            "works.",
      value=None, authority="SEAI",
      source_title="Solar electricity grant (solar PV)", source_url=SEAI_SOLAR,
      source_type="SCHEME_PAGE", maturity="CURRENT_RULE",
      staleness_policy="WITHHOLD", homeowner_safe=True, logic_safe=False,
      notes="Quoted verbatim from SEAI. WITHHOLD rather than downgrade: if the "
            "wording changes we must stop quoting it, not soften it."),

    # =======================================================================
    # TIME
    # =======================================================================
    r(evidence_id="time-meter-enables-tou", opportunity="TIME",
      claim_key="meter_enables_time_of_use",
      claim="A smart meter gives access to smart and time-of-use tariff options.",
      value={"enables": True}, authority="CRU",
      source_title="CRU Microgeneration Q&A (CRU/202366)", source_url=CRU_QA,
      source_type="REGULATOR_DECISION", source_published_date="2023-06-26",
      maturity="CURRENT_RULE", homeowner_safe=True, logic_safe=True),

    r(evidence_id="time-meter-not-tariff", opportunity="TIME",
      claim_key="meter_is_not_tariff",
      claim="Having a smart meter installed does not mean being on a "
            "time-of-use tariff; that is a separate choice with the supplier.",
      value={"automatic": False}, authority="CRU",
      source_title="CRU Chairperson, quoted in ESB smart meter release",
      source_url=ESB_SMART, source_type="PRESS_RELEASE",
      source_published_date="2025-09-04", maturity="CURRENT_RULE",
      homeowner_safe=True, logic_safe=True,
      notes="The most common homeowner misunderstanding in this journey."),

    r(evidence_id="time-rollout-penetration", opportunity="TIME",
      claim_key="smart_meter_rollout_floor",
      claim="Over two million smart meters are installed and more than four out "
            "of five households have one.",
      value={"meters_installed_min": 2000000, "household_share_min": 0.8,
             "as_at": "2025-09-04"},
      authority="ESB_NETWORKS",
      source_title="Over two million smart meters installed nationwide",
      source_url=ESB_SMART, source_type="PRESS_RELEASE",
      source_published_date="2025-09-04", review_interval_months=12,
      maturity="CURRENT_RULE", homeowner_safe=True, logic_safe=False,
      notes="POPULATION STATISTIC. logic_safe=false by design: it must never "
            "be used to infer that a particular home has a meter. Both figures "
            "are floors, and the rollout continues."),

    # =======================================================================
    # STORE
    # =======================================================================
    r(evidence_id="store-no-seai-grant", opportunity="STORE",
      claim_key="battery_grant_exists",
      claim="There is no SEAI grant for home battery storage.",
      value={"grant_exists": False}, authority="SEAI",
      source_title="Home energy grants — published measures", source_url=SEAI_HOME,
      source_type="SCHEME_PAGE", review_interval_months=6,
      maturity="CURRENT_SCHEME", homeowner_safe=True, logic_safe=True,
      notes="A NEGATIVE claim. Re-checked on a 6-month cycle because a stale "
            "negative costs a homeowner money as surely as a stale positive."),

    r(evidence_id="store-battery-recognised", opportunity="STORE",
      claim_key="battery_recognised_renewable",
      claim="Electricity from a renewable source stored in a battery and used, "
            "or exported later, is still treated as renewable.",
      value=None, authority="CRU",
      source_title="CRU Microgeneration Q&A (CRU/202366)", source_url=CRU_QA,
      source_type="REGULATOR_DECISION", source_published_date="2023-06-26",
      maturity="CURRENT_REGULATORY_REQUIREMENT",
      homeowner_safe=False, logic_safe=False),

    r(evidence_id="store-ac-bess-is-microgen", opportunity="STORE",
      claim_key="ac_battery_treated_as_microgeneration",
      claim="An AC-connected battery is considered a microgenerator for ESB "
            "Networks purposes.",
      value={"treated_as_microgeneration": True}, authority="ESB_NETWORKS",
      source_title="Quick User Guide: Microgeneration & Smart Battery Energy "
                   "Storage (DOC-301121-HFX)",
      source_url=ESBN_BESS, source_type="OPERATOR_STANDARD",
      source_published_date="2021-11-30", review_interval_months=12,
      maturity="CURRENT_REGULATORY_REQUIREMENT",
      homeowner_safe=True, logic_safe=True),

    r(evidence_id="store-notification-required", opportunity="STORE",
      claim_key="battery_requires_esbn_notification",
      claim="ESB Networks is notified before the battery is installed.",
      value={"in_advance": True}, authority="ESB_NETWORKS",
      source_title="Quick User Guide: Microgeneration & Smart Battery Energy "
                   "Storage (DOC-301121-HFX)",
      source_url=ESBN_BESS, source_type="OPERATOR_STANDARD",
      source_published_date="2021-11-30", review_interval_months=12,
      maturity="CURRENT_REGULATORY_REQUIREMENT",
      homeowner_safe=True, logic_safe=True),

    r(evidence_id="store-nc6-within-thresholds", opportunity="STORE",
      claim_key="battery_nc6_within_thresholds",
      claim="An AC-connected battery is listed on the ESB Networks NC6 "
            "application with its rated output, within the microgeneration "
            "thresholds.",
      value={"single_phase_amps_max": 25, "three_phase_amps_max": 16,
             "assessed_on": "inverter_capacity"},
      authority="ESB_NETWORKS",
      source_title="Conditions Governing the Connection and Operation of "
                   "Micro-Generation (DTIS-230206-BRL v6.1)",
      source_url=ESBN_COND, source_type="OPERATOR_STANDARD",
      source_published_date="2021-12-03", review_interval_months=12,
      maturity="CURRENT_REGULATORY_REQUIREMENT",
      homeowner_safe=False, logic_safe=False,
      notes="homeowner_safe=false: NC6, amps and kVA are installer vocabulary. "
            "The reveal says ESB Networks is told first; the form is detail. "
            "logic_safe=false: the frozen V1 journey does not gate on the "
            "threshold, so marking it engine-facing would be dead surface."),

    r(evidence_id="store-safe-electric-required", opportunity="STORE",
      claim_key="battery_requires_safe_electric_rec",
      claim="The AC system must be tested and certified by a Registered "
            "Electrical Contractor, and a Safe Electric certificate provided.",
      value={"safe_electric_rec_required": True}, authority="ESB_NETWORKS",
      source_title="Quick User Guide: Microgeneration & Smart Battery Energy "
                   "Storage (DOC-301121-HFX)",
      source_url=ESBN_BESS, source_type="OPERATOR_STANDARD",
      source_published_date="2021-11-30", review_interval_months=12,
      maturity="CURRENT_REGULATORY_REQUIREMENT",
      homeowner_safe=True, logic_safe=True),

    r(evidence_id="store-certification-required", opportunity="STORE",
      claim_key="battery_requires_certification",
      claim="Type-test certification to I.S. EN 50549-1 and a protection-"
            "settings confirmation certificate are required, and copies are "
            "given to the customer.",
      value={"type_test": True, "protection_settings_cert": True},
      authority="ESB_NETWORKS",
      source_title="Conditions Governing the Connection and Operation of "
                   "Micro-Generation (DTIS-230206-BRL v6.1)",
      source_url=ESBN_COND, source_type="OPERATOR_STANDARD",
      source_published_date="2021-12-03", review_interval_months=12,
      maturity="CURRENT_REGULATORY_REQUIREMENT",
      homeowner_safe=False, logic_safe=False),

    r(evidence_id="store-capacity-determines-route", opportunity="STORE",
      claim_key="battery_route_by_capacity",
      claim="Inverter or aggregate capacity determines which connection route "
            "applies; requirements are not identical for every installation.",
      value=None, authority="ESB_NETWORKS",
      source_title="Conditions Governing the Connection and Operation of "
                   "Micro-Generation (DTIS-230206-BRL v6.1)",
      source_url=ESBN_COND, source_type="OPERATOR_STANDARD",
      source_published_date="2021-12-03", review_interval_months=12,
      maturity="CURRENT_REGULATORY_REQUIREMENT",
      homeowner_safe=True, logic_safe=False,
      notes="RESIDUAL LIMITATION, recorded and NOT generalised: the reviewed "
            "ESB Networks material does not establish the treatment of a "
            "battery genuinely incapable of exporting or operating in parallel "
            "with the distribution network. Nothing is inferred either way, and "
            "this edge case must not become a universal rule."),

    # =======================================================================
    # SELL
    # =======================================================================
    r(evidence_id="sell-ceg-obligation", opportunity="SELL",
      claim_key="supplier_must_pay_for_export",
      claim="Every electricity supplier must pay for eligible electricity "
            "exported to the grid.",
      value={"obligation": True}, authority="CRU",
      source_title="CRU Microgeneration Q&A (CRU/202366)", source_url=CRU_QA,
      source_type="REGULATOR_DECISION", source_published_date="2023-06-26",
      valid_from="2022-02-15", maturity="CURRENT_REGULATORY_REQUIREMENT",
      homeowner_safe=True, logic_safe=True,
      notes="The scheme is styled INTERIM Clean Export Guarantee (CRU21131). "
            "The word interim is itself a standing review signal."),

    r(evidence_id="sell-state-a", opportunity="SELL",
      claim_key="export_state_metered",
      claim="With a smart meter and a processed NC6 or NC7, the supplier pays "
            "for every metered unit exported.",
      value={"state": "A"}, authority="CRU",
      source_title="CRU Microgeneration Q&A (CRU/202366), Q7", source_url=CRU_QA,
      source_type="REGULATOR_DECISION", source_published_date="2023-06-26",
      maturity="CURRENT_REGULATORY_REQUIREMENT",
      homeowner_safe=True, logic_safe=True),

    r(evidence_id="sell-state-b", opportunity="SELL",
      claim_key="export_state_waiting",
      claim="Where the home is eligible for a smart meter and waiting, payment "
            "is not made while waiting and begins when the meter is installed.",
      value={"state": "B"}, authority="CRU",
      source_title="CRU Microgeneration Q&A (CRU/202366), Q7", source_url=CRU_QA,
      source_type="REGULATOR_DECISION", source_published_date="2023-06-26",
      maturity="CURRENT_REGULATORY_REQUIREMENT",
      homeowner_safe=False, logic_safe=True,
      notes="Not separated from state C at the surface: meter eligibility is "
            "ESB Networks' determination, not a fact the homeowner holds."),

    r(evidence_id="sell-state-c", opportunity="SELL",
      claim_key="export_state_calculated",
      claim="Where the home is not yet eligible for a smart meter, the supplier "
            "pays on a calculated export quantity instead.",
      value={"state": "C"}, authority="CRU",
      source_title="CRU Microgeneration Q&A (CRU/202366), Q7", source_url=CRU_QA,
      source_type="REGULATOR_DECISION", source_published_date="2023-06-26",
      maturity="CURRENT_REGULATORY_REQUIREMENT",
      homeowner_safe=True, logic_safe=True,
      notes="The regulator's term is 'deemed export quantity'. The journey says "
            "'a calculated amount' — same meaning, no jargon."),

    r(evidence_id="sell-state-d", opportunity="SELL",
      claim_key="export_state_declined",
      claim="Where a smart meter has been offered and refused, the home is not "
            "eligible for export payment.",
      value={"state": "D"}, authority="CRU",
      source_title="CRU Microgeneration Q&A (CRU/202366), Q10", source_url=CRU_QA,
      source_type="REGULATOR_DECISION", source_published_date="2023-06-26",
      maturity="CURRENT_REGULATORY_REQUIREMENT",
      homeowner_safe=True, logic_safe=True,
      notes="The only FALSE in the journey. An UNKNOWN meter answer must never "
            "resolve here."),

    r(evidence_id="sell-nc6-gates-payment", opportunity="SELL",
      claim_key="export_requires_registration",
      claim="Without the NC6 or NC7 processed by ESB Networks, the supplier "
            "will not pay for exported electricity.",
      value={"registration_required": True}, authority="CRU",
      source_title="CRU Microgeneration Q&A (CRU/202366), Q5", source_url=CRU_QA,
      source_type="REGULATOR_DECISION", source_published_date="2023-06-26",
      maturity="CURRENT_REGULATORY_REQUIREMENT",
      homeowner_safe=True, logic_safe=True),

    r(evidence_id="sell-rates-unregulated", opportunity="SELL",
      claim_key="export_rates_unregulated",
      claim="Each supplier sets its own export rate; the rates are open to "
            "competition and are not regulated.",
      value={"regulated": False}, authority="CRU",
      source_title="CRU Microgeneration Q&A (CRU/202366), Q11", source_url=CRU_QA,
      source_type="REGULATOR_DECISION", source_published_date="2023-06-26",
      maturity="CURRENT_REGULATORY_REQUIREMENT",
      homeowner_safe=True, logic_safe=True,
      notes="NO RATE IS STORED IN THIS MANIFEST, at any time, for any supplier."),

    r(evidence_id="sell-meter-install-target", opportunity="SELL",
      claim_key="meter_install_target_after_nc6",
      claim="Where the home is eligible, ESB Networks endeavours to install a "
            "smart meter within four months of a processed NC6, and a "
            "prioritised installation can be requested.",
      value={"months": 4}, authority="CRU",
      source_title="CRU Microgeneration Q&A (CRU/202366), Q9", source_url=CRU_QA,
      source_type="REGULATOR_DECISION", source_published_date="2023-06-26",
      maturity="CURRENT_REGULATORY_REQUIREMENT",
      homeowner_safe=True, logic_safe=False),

    r(evidence_id="sell-tax-exemption", opportunity="SELL",
      claim_key="microgen_income_tax_exemption",
      claim="The first EUR 400 a year of microgeneration income is exempt from "
            "income tax.",
      value={"amount": 400, "currency": "EUR", "per": "year"},
      authority="REVENUE", source_title="Micro-generation", source_url=CI_MICRO,
      source_type="TAX_RULE", source_published_date="2025-10-08",
      valid_from="2024-01-01", valid_until="2028-12-31",
      maturity="TIME_LIMITED", staleness_policy="SAFE_UNTIL_EXPIRY",
      homeowner_safe=True, logic_safe=True,
      notes="Withholds itself on 2029-01-01. Any replacement must be VERIFIED, "
            "never inferred."),

    r(evidence_id="sell-mss-eligibility", opportunity="SELL",
      claim_key="mss_eligibility",
      claim="To qualify, the home must have solar panels, have been built "
            "before 2021, have an MPRN, and be registered with an electricity "
            "supplier. No minimum BER applies.",
      value={"requires_generation": True, "before_year": 2021,
             "mprn_required": True, "minimum_ber": None},
      authority="CITIZENS_INFO", source_title="Micro-generation",
      source_url=CI_MICRO, source_type="SECONDARY",
      source_published_date="2025-10-08", maturity="CURRENT_SCHEME",
      homeowner_safe=True, logic_safe=True),
]


# ===========================================================================
# STALENESS RESOLUTION — architecture §11.4, first match wins
# ===========================================================================
def months_between(a: date, b: date) -> int:
    return (b.year - a.year) * 12 + (b.month - a.month) - (1 if b.day < a.day else 0)


def resolve(rec, as_of: date):
    """Compute resolved_status. Order matters and is the architecture's."""
    def d(field):
        return datetime.strptime(rec[field], "%Y-%m-%d").date() if rec.get(field) else None

    if rec.get("superseded_by"):
        return "SUPERSEDED", "superseded_by is set"
    if rec.get("conflicts_with"):
        return "WITHHOLD", "conflicts with another authoritative record"
    if not rec.get("source_reachable", True):
        return "WITHHOLD", "source was unreachable at last review"

    vf = d("valid_from")
    if rec["maturity"] == "ANNOUNCED_FUTURE_CHANGE" and (vf is None or vf > as_of):
        return "NOT_YET_IN_FORCE", "announced, not yet in force"

    vu = d("valid_until")
    if vu and vu < as_of:
        if rec["staleness_policy"] == "SAFE_UNTIL_EXPIRY":
            return "WITHHOLD", f"expired on {rec['valid_until']}"
        if rec["staleness_policy"] == "WITHHOLD":
            return "WITHHOLD", f"expired on {rec['valid_until']}"
        return "RECHECK_REQUIRED", f"expired on {rec['valid_until']}"

    lv = d("last_verified")
    if lv and months_between(lv, as_of) >= rec["review_interval_months"]:
        return "RECHECK_REQUIRED", "verification interval elapsed"

    return "CURRENT", None


def build(as_of: date):
    out = []
    for rec in RECORDS:
        rec = dict(rec)
        status, why = resolve(rec, as_of)
        rec["resolved_status"] = status
        rec["resolved_reason"] = why
        # A record that is not CURRENT can never be served as current evidence,
        # whatever its own flags say. Enforced here so the client cannot differ.
        if status != "CURRENT":
            rec["homeowner_safe_resolved"] = False
            rec["logic_safe_resolved"] = False
        else:
            rec["homeowner_safe_resolved"] = rec["homeowner_safe"]
            rec["logic_safe_resolved"] = rec["logic_safe"]
        out.append(rec)
    return {
        "schema": SCHEMA,
        "generated": as_of.isoformat(),
        "jurisdiction": "IE-ROI",
        "governing_architecture_sha256": "SEE DISC-026-JOURNEY-ARCHITECTURE.md",
        "opportunities": ["MAKE", "TIME", "STORE", "SELL"],
        "recordCount": len(out),
        "note": "Generated by .github/scripts/generate_disc026_evidence.py. "
                "Do not hand-edit. Staleness is resolved at generation time so "
                "no two clients can disagree about what is current.",
        "records": out,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=None)
    ap.add_argument("--as-of", default=date.today().isoformat())
    a = ap.parse_args()
    as_of = datetime.strptime(a.as_of, "%Y-%m-%d").date()
    doc = build(as_of)
    text = json.dumps(doc, indent=2, ensure_ascii=False) + "\n"
    if a.out:
        Path(a.out).write_text(text, encoding="utf-8")
        counts = {}
        for r_ in doc["records"]:
            counts[r_["resolved_status"]] = counts.get(r_["resolved_status"], 0) + 1
        print(f"  wrote {a.out}")
        print(f"  as-of           : {as_of}")
        print(f"  records         : {doc['recordCount']}")
        print(f"  resolved        : {counts}")
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
