#!/usr/bin/env python3
"""
PlotNua — DISC-026 SUPPLIER EXPORT evidence manifest GENERATOR (Stage 3 pilot).

    generate_supplier_export_evidence.py [--out FILE] [--as-of YYYY-MM-DD]

WHAT THIS IS.

  The DISC-026 manifest (plotnua.disc026.evidence.v1) governs the NATIONAL
  RULES: SEAI grants, CRU export obligations, ESB Networks requirements, tax,
  VAT, planning. Those are single national schemes and they stay there.

  What it cannot hold is the part that VARIES BY ORGANISATION. Its own record
  `export_rates_unregulated` says so:

      "Each supplier sets its own export rate; the rates are open to
       competition and are not regulated."

  So the rules manifest establishes that the number differs by supplier, and
  holds not one instance of it. This manifest holds those instances, and
  nothing else. It does not restate a single national rule.

CANONICAL EVIDENCE MODEL.

  Same decomposition as plotnua.parking-platform.evidence.v2: authority,
  source_type, evidence_type, verification_method, verification_status,
  maturity, validity/staleness, provenance, claim_basis, homeowner_safe,
  logic_safe. `evidence_state_derived` is computed, never stored as truth.

  Every supplier proposition here is claim_basis = STATED. The supplier
  publishes it. PlotNua has not observed a payment, so nothing is
  OPERATIONAL, and the generator refuses to emit an OPERATIONAL claim.

THE VAT FIREWALL — THE REASON THIS PILOT IS SHAPED THIS WAY.

  Only Flogas publishes a VAT basis (EUR 0.185 exc. VAT / EUR 0.20 inc. VAT at
  9%). Three of four suppliers publish a rate with no basis at all.

  The VAT adjustment is about 1.7c. The entire spread between suppliers is
  about 1c. So VAT basis is LARGER THAN THE DIFFERENCE BEING COMPARED, and a
  naive table would rank suppliers in the wrong order.

  This file therefore contains NO ranking, NO normalisation, NO "best rate"
  and NO derived annual earnings. `comparable_rates()` exists only to refuse,
  in one place, with a reason. A rate is recorded on the basis the supplier
  actually published, and where no basis is published the basis is UNKNOWN and
  stays UNKNOWN.

PAYMENT MECHANISM IS NOT FLATTENED EITHER.

  "credit on each bill", "credit on your invoice rather than a direct bank
  transfer", "account credited at the same frequency as the regular bill" and
  "payable four times a year" are four different statements. They are recorded
  as each source puts them, never collapsed into "bill credit".

NOT homeowner-facing. NOT wired to the DISC-026 journey. No imagery of any
kind: no logo, no photograph, no hotlink, no Asset record.

Edit the records below; never hand-edit the JSON.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime
from pathlib import Path

SCHEMA = "plotnua.disc026.supplier-export.evidence.v1"
JURISDICTION = "IE-ROI"
VERIFIED_ON = "2026-09-22"

CLAIM_BASIS = {"STATED", "OPERATIONAL"}
EVIDENCE_TYPE = {"PUBLISHED_SOURCE", "ABSENCE_OF_RECORD", "CONFLICTING_SOURCES",
                 "UNTESTED", "CORRESPONDENCE"}
SOURCE_TYPE = {"SUPPLIER_TARIFF_PAGE", "SUPPLIER_HELP_CONTENT",
               "SUPPLIER_MARKETING_CLAIM", "CORPORATE_REGISTER", "OUTREACH_RECORD"}
PROVENANCE = {"PUBLIC_PRIMARY", "SUPPLIER_PROVIDED", "COMMERCIAL_CORRESPONDENCE"}
MATURITY = {"CURRENT_PUBLISHED", "BOUNDED_SEARCH", "NOT_ESTABLISHABLE",
            "UNRESOLVED_CONFLICT"}
NEVER_LOGIC_SAFE_TYPES = {"ABSENCE_OF_RECORD", "UNTESTED", "CONFLICTING_SOURCES"}

# ── the four pilot suppliers ────────────────────────────────────────────────
# Evidence-shaped, NOT a commercial ranking and never to be presented as one.
SUPPLIERS = {
    "electric-ireland": {
        "supplier_name": "Electric Ireland",
        "atlas_organisation_code": "ORG-ESUP-EI",
        "source": ("Electric Ireland — Microgeneration for Homes",
                   "https://www.electricireland.ie/residential/products/microgeneration"),
        "selected_because": "explicit customer-of-supplier and smart-meter eligibility",
    },
    "bord-gais-energy": {
        "supplier_name": "Bord Gáis Energy",
        "atlas_organisation_code": "ORG-ESUP-BGE",
        "source": ("Bord Gáis Energy — Microgeneration",
                   "https://www.bordgaisenergy.ie/home/microgeneration"),
        "selected_because": "only pilot supplier evidencing deemed-export treatment",
    },
    "energia": {
        "supplier_name": "Energia",
        "atlas_organisation_code": "ORG-ESUP-ENERGIA",
        "source": ("Energia — Microgeneration Scheme",
                   "https://www.energia.ie/home-upgrades/energia-and-the-microgeneration-scheme"),
        "selected_because": "fullest eligibility list and an explicit non-cash payment statement",
    },
    "flogas": {
        "supplier_name": "Flogas",
        "atlas_organisation_code": "ORG-ESUP-FLOGAS",
        "source": ("Flogas — Micro-generation",
                   "https://www.flogas.ie/help-centre/flogas-micro-generation/"),
        "selected_because": "only pilot supplier publishing a VAT basis and an effective date",
    },
}

PILOT_NOTE = (
    "Controlled architectural pilot. Four suppliers, selected to expose "
    "different EVIDENCE SHAPES — VAT basis, deemed export, eligibility "
    "conditions, payment mechanism. This is NOT a ranking, NOT a "
    "recommendation and NOT a statement that these are the best or only "
    "suppliers. Two further qualifying suppliers (SSE Airtricity, Pinergy) "
    "were deliberately excluded from this stage."
)


def claim(supplier, key, text, value, *, basis="STATED",
          evidence_type="PUBLISHED_SOURCE", source_type="SUPPLIER_TARIFF_PAGE",
          provenance="PUBLIC_PRIMARY", maturity="CURRENT_PUBLISHED",
          quote=None, effective_date=None, months=3,
          method="PRIMARY_FETCH", homeowner_safe=True, logic_safe=True,
          triggers=None, prohibited=None, limitations=None, notes=None):
    s = SUPPLIERS[supplier]
    title, url = s["source"]
    return {
        "supplier_key": supplier,
        "supplier_name": s["supplier_name"],
        "atlas_organisation_code": s["atlas_organisation_code"],
        "claim_key": f"{supplier}::{key}",
        "claim_field": key,
        "claim": text,
        "value": value,
        "claim_basis": basis,
        "authority": s["supplier_name"],
        "source_type": source_type,
        "evidence_type": evidence_type,
        "maturity": maturity,
        "provenance": provenance,
        "verification_method": method,
        "source_title": title,
        "source_url": url,
        "quote": quote,
        "last_verified": VERIFIED_ON,
        "effective_date": effective_date,
        "valid_until": None,
        "review_interval_months": months,
        "staleness_policy": "DOWNGRADE",
        "recheck_triggers": triggers or [],
        "prohibited_readings": prohibited or [],
        "limitations": limitations or [],
        "homeowner_safe": homeowner_safe,
        "logic_safe": logic_safe,
        "notes": notes,
    }


def absent(supplier, key, text, **kw):
    """Searched the supplier's own published source; the claim is not there."""
    kw.setdefault("logic_safe", False)
    return claim(supplier, key, text, None, evidence_type="ABSENCE_OF_RECORD",
                 maturity="BOUNDED_SEARCH", method="TARGETED_SEARCH", **kw)


VAT_UNKNOWN_PROHIBITED = [
    "Any inference that the published rate is VAT-inclusive or VAT-exclusive.",
    "Any comparison, ranking or normalisation of this rate against another "
    "supplier's rate while the VAT basis is UNKNOWN.",
]

C = []

# ── ELECTRIC IRELAND ────────────────────────────────────────────────────────
s = "electric-ireland"
C += [
    claim(s, "export_proposition",
          "Eligible domestic microgeneration customers are paid for exported "
          "electricity under the Microgeneration Support Scheme / CEG.",
          {"offered": True},
          quote=("The Government Microgeneration Support Scheme allows households "
                 "with a registered microgeneration device to sell any excess "
                 "electricity back to Ireland's electricity grid.")),
    claim(s, "export_rate",
          "Published Microgen export rate.",
          {"amount": 19.5, "unit": "c/kWh", "as_published": "19.5c per kWh"},
          quote="Electric Ireland's current Microgen Export rate is 19.5c per kWh.",
          prohibited=VAT_UNKNOWN_PROHIBITED),
    absent(s, "export_rate_vat_basis",
           "Whether the published rate is inclusive or exclusive of VAT.",
           prohibited=VAT_UNKNOWN_PROHIBITED,
           notes=("Not stated anywhere on the supplier's microgeneration page. "
                  "At 9% VAT this is ~1.7c, which exceeds the ~1c spread "
                  "between pilot suppliers.")),
    claim(s, "rate_variability",
          "The supplier warns the rate may change.",
          {"variable": True},
          quote="This rate is variable and subject to change."),
    absent(s, "rate_effective_date", "The date the published rate took effect."),
    claim(s, "customer_of_supplier_required",
          "Only the supplier's own customers are eligible.",
          {"required": True},
          quote=("Only Electric Ireland customers who meet the criteria above "
                 "are eligible for the Microgeneration Scheme through Electric "
                 "Ireland.")),
    claim(s, "smart_meter_required",
          "A smart meter is required.",
          {"required": True},
          source_type="SUPPLIER_HELP_CONTENT",
          quote=("In line with guidelines provided by CRU, a smart meter is "
                 "required to avail of The Microgeneration Support Scheme.")),
    claim(s, "connection_requirement",
          "An export grid connection and a registered NC6 are required.",
          {"nc6": True, "export_grid_connection": True},
          quote=("You must have an export grid connection… Your solar PV "
                 "installer would have registered an NC6 form on your behalf to "
                 "ESB Networks.")),
    absent(s, "deemed_export_treatment",
           "Whether export is paid where the home cannot have a smart meter."),
    claim(s, "payment_mechanism",
          "How the benefit reaches the customer, in the supplier's own words.",
          {"as_published": "microgeneration credit on each bill"},
          source_type="SUPPLIER_HELP_CONTENT",
          quote=("you will then receive a microgeneration credit on each bill "
                 "thereafter in line with your billing cycle"),
          prohibited=["Restating this as a generic 'bill credit' shared with "
                      "other suppliers."]),
    claim(s, "payment_frequency",
          "How often the credit is applied.",
          {"as_published": "in line with your billing cycle"},
          source_type="SUPPLIER_HELP_CONTENT",
          quote="in line with your billing cycle"),
    claim(s, "indicative_annual_earnings",
          "The supplier's own indicative earnings estimate.",
          {"range_eur": [50, 300], "typical_example": "10 panels ≈ €150 per year"},
          source_type="SUPPLIER_MARKETING_CLAIM", logic_safe=False,
          quote=("We estimate that customer export payments will range between "
                 "€50-€300 per year… a typical installation of 10 panels would "
                 "be about €150 per year"),
          prohibited=["Any use of this figure as a PlotNua calculation or as a "
                      "comparison against another supplier."],
          notes="Supplier marketing estimate, not a PlotNua computation."),
    absent(s, "caps_minimum_terms_exclusions",
           "Published caps, minimum terms or exclusions."),
]

# ── BORD GÁIS ENERGY ────────────────────────────────────────────────────────
s = "bord-gais-energy"
C += [
    claim(s, "export_proposition",
          "Eligible customers are paid for exported electricity under the "
          "supplier's Microgen Export Plan.",
          {"offered": True, "plan_name": "Microgen Export Plan"},
          quote=("18.5 cent per kWh for any excess electricity that they are "
                 "microgenerating and exporting to the electricity grid under "
                 "our Microgen Export Plan")),
    claim(s, "export_rate", "Published export rate.",
          {"amount": 18.5, "unit": "c/kWh", "as_published": "18.5 cent per kWh"},
          quote="18.5 cent per kWh",
          prohibited=VAT_UNKNOWN_PROHIBITED),
    absent(s, "export_rate_vat_basis",
           "Whether the published rate is inclusive or exclusive of VAT.",
           prohibited=VAT_UNKNOWN_PROHIBITED),
    absent(s, "rate_variability",
           "An explicit warning that the rate may change."),
    absent(s, "rate_effective_date", "The date the published rate took effect.",
           notes="The page carries 'Updated October 2025' but dates the page, not the rate."),
    claim(s, "deemed_export_supported",
          "The rate is offered to metered customers AND to eligible deemed "
          "customers — the only pilot supplier evidencing this.",
          {"metered": True, "deemed": True},
          quote=("This rate will be offered to both metered and eligible "
                 "deemed* customers."),
          notes=("Corresponds to CRU export state C in the DISC-026 rules "
                 "manifest. Materially different from a price difference: for a "
                 "home that cannot have a smart meter this is the difference "
                 "between being paid and not being paid.")),
    claim(s, "deemed_export_definition",
          "How a deemed customer is defined and how export is calculated.",
          {"definition": "not eligible under the National Smart Metering Programme",
           "calculation": "pre-determined formula"},
          quote=("Deemed customers are customers who are not eligible under the "
                 "National Smart Metering Program to have a smart meter "
                 "installed. In this case, your export amount will be "
                 "calculated (deemed) using a pre-determined formula.")),
    claim(s, "smart_meter_required",
          "A smart meter is required only where the home is eligible for one.",
          {"required": "conditional", "condition": "if eligible for a smart meter"},
          quote=("If you're eligible for a smart meter, you'll need to have one "
                 "installed to qualify for a payment.")),
    claim(s, "terms_agreement_required",
          "The customer must agree to the plan's terms and conditions.",
          {"required": True},
          quote="To receive a payment, you'll need to agree to our Microgen Export Plan T&Cs"),
    claim(s, "payment_mechanism",
          "How the benefit reaches the customer, in the supplier's own words.",
          {"as_published": "a credit to your electricity bill"},
          quote="payments will be made 4 times per year as a credit to your electricity bill",
          prohibited=["Restating this as a generic 'bill credit' shared with "
                      "other suppliers."]),
    claim(s, "payment_frequency",
          "How often payment is made, and the qualifying period before it starts.",
          {"as_published": "4 times per year",
           "qualifying_period": "after at least 3 months of export"},
          quote="Once you've exported for at least 3 months, payments will be made 4 times per year"),
    claim(s, "backdating",
          "Payments are back-dated to legislation date or to eligibility.",
          {"legislation_date": "2022-02-15"},
          quote=("If you were a Bord Gáis Energy customer on February 15th 2022 "
                 "(date of legislation) and microgenerating at that time, your "
                 "payment will be back-dated.")),
    absent(s, "customer_of_supplier_required",
           "Whether only the supplier's own customers are eligible.",
           notes="Implied by 'our Microgen Export Plan' but not explicitly stated."),
    absent(s, "caps_minimum_terms_exclusions",
           "Published caps, minimum terms or exclusions."),
]

# ── ENERGIA ─────────────────────────────────────────────────────────────────
s = "energia"
C += [
    claim(s, "export_proposition",
          "Eligible customers receive credit for exported electricity under the "
          "supplier's Microgeneration Scheme / CEG.",
          {"offered": True, "plan_name": "Energia Microgeneration Scheme"},
          quote=("Energia currently offers a competitive rate of 18.5 cent "
                 "(18.5c/kWh) for every unit of surplus electricity you export "
                 "back to the grid.")),
    claim(s, "export_rate", "Published export rate.",
          {"amount": 18.5, "unit": "c/kWh", "as_published": "18.5 cent (18.5c/kWh)"},
          quote="Energia currently offers a microgeneration rate of 18.5 cent (18.5c/kWh).",
          prohibited=VAT_UNKNOWN_PROHIBITED),
    absent(s, "export_rate_vat_basis",
           "Whether the published rate is inclusive or exclusive of VAT.",
           prohibited=VAT_UNKNOWN_PROHIBITED),
    absent(s, "rate_variability",
           "An explicit warning that the rate may change.",
           notes="The page says 'currently offers', which is not a change warning."),
    absent(s, "rate_effective_date", "The date the published rate took effect."),
    claim(s, "eligibility_conditions",
          "Published eligibility conditions for joining the scheme.",
          {"conditions": ["own a microgenerator such as a solar PV system",
                          "have an export grid connection",
                          "have a smart meter installed",
                          "submit the NC6 form to ESBN"]},
          quote=("To join Energia's Microgeneration Scheme, you must: Own a "
                 "microgenerator… Have an export grid connection… Have a smart "
                 "meter installed (Energia can request one for you)… Submit the "
                 "NC6 form to ESBN")),
    claim(s, "smart_meter_required", "A smart meter is required.",
          {"required": True, "supplier_can_request": True},
          quote="Have a smart meter installed (Energia can request one for you)"),
    claim(s, "connection_requirement",
          "An export grid connection and an NC6 submission are required.",
          {"nc6": True, "export_grid_connection": True},
          quote="Submit the NC6 form to ESBN (your installer may do this for you)"),
    claim(s, "payment_mechanism",
          "How the benefit reaches the customer — explicitly NOT a bank transfer.",
          {"as_published": "a credit on your invoice rather than a direct bank transfer"},
          quote=("This exported energy is compensated through the Clean Export "
                 "Guarantee (CEG) tariff, applied as a credit on your invoice "
                 "rather than a direct bank transfer."),
          prohibited=["Restating this as a generic 'bill credit' shared with "
                      "other suppliers."],
          notes="The only pilot supplier that explicitly rules out cash payment."),
    claim(s, "payment_frequency", "How often the credit is applied.",
          {"as_published": "bi-monthly electricity bill"},
          quote=("you'll receive a credit on your bi-monthly electricity bill "
                 "for any excess renewable electricity you export to the grid")),
    claim(s, "metering_basis", "How export is measured.",
          {"as_published": "readings taken every 30 minutes, sent to ESBN"},
          quote=("Thanks to your smart meter, readings are taken every 30 "
                 "minutes and automatically sent to ESBN.")),
    claim(s, "billing_period_limitation",
          "The supplier warns export and import periods may differ.",
          {"as_published": "export period may differ from import period"},
          homeowner_safe=True, logic_safe=False,
          quote=("The export period shown on your bill might sometimes differ "
                 "from your import period due to ESBN data delivery timings.")),
    absent(s, "deemed_export_treatment",
           "Whether export is paid where the home cannot have a smart meter."),
    absent(s, "customer_of_supplier_required",
           "Whether only the supplier's own customers are eligible."),
    absent(s, "caps_minimum_terms_exclusions",
           "Published caps, minimum terms or exclusions."),
]

# ── FLOGAS ──────────────────────────────────────────────────────────────────
s = "flogas"
C += [
    claim(s, "export_proposition",
          "An export tariff is applied to excess exported electricity.",
          {"offered": True},
          source_type="SUPPLIER_HELP_CONTENT",
          quote=("An export tariff rate of €0.185 (exc. VAT), €0.20 (inc. VAT "
                 "at 9%) per kWh will be applied to the excess exported "
                 "electricity.")),
    claim(s, "export_rate", "Published export rate, on both VAT bases.",
          {"amount_exc_vat": 0.185, "amount_inc_vat": 0.20, "currency": "EUR",
           "unit": "per kWh",
           "as_published": "€0.185 (exc. VAT), €0.20 (inc. VAT at 9%) per kWh"},
          source_type="SUPPLIER_HELP_CONTENT", effective_date="2023-11-06",
          quote=("An export tariff rate of €0.185 (exc. VAT), €0.20 (inc. VAT "
                 "at 9%) per kWh")),
    claim(s, "export_rate_vat_basis",
          "The VAT basis is published — the only pilot supplier to do so.",
          {"exclusive": 0.185, "inclusive": 0.20, "vat_rate_percent": 9},
          source_type="SUPPLIER_HELP_CONTENT",
          quote="€0.185 (exc. VAT), €0.20 (inc. VAT at 9%)",
          notes=("Establishes the scale of the problem for the other three: a "
                 "~1.7c VAT adjustment against a ~1c spread between suppliers.")),
    claim(s, "rate_effective_date", "The date the published rate took effect.",
          {"date": "2023-11-06"}, source_type="SUPPLIER_HELP_CONTENT",
          effective_date="2023-11-06",
          quote="Effective date of the rate is 6 November 2023.",
          limitations=["A third-party source located during research stated an "
                       "effective date of 24 June 2025. The supplier's own page "
                       "states 6 November 2023. Only the first-party date is "
                       "recorded."]),
    claim(s, "rate_variability", "The supplier reserves the right to change the rate.",
          {"variable": True}, source_type="SUPPLIER_HELP_CONTENT",
          quote="Flogas reserve the right to vary rates."),
    claim(s, "payment_mechanism",
          "How the benefit reaches the customer, in the supplier's own words.",
          {"as_published": "account credited at the same frequency as the regular bill"},
          source_type="SUPPLIER_HELP_CONTENT",
          quote=("Flogas will credit your electricity account at the same "
                 "frequency and time as your regular bill"),
          prohibited=["Restating this as a generic 'bill credit' shared with "
                      "other suppliers."]),
    claim(s, "payment_frequency", "How often the credit is applied.",
          {"as_published": "same frequency and time as your regular bill"},
          source_type="SUPPLIER_HELP_CONTENT",
          quote="at the same frequency and time as your regular bill"),
    absent(s, "eligibility_conditions",
           "Published eligibility conditions.",
           notes=("An 'What is the Eligibility Criteria?' section exists on the "
                  "page but its content was not captured in this pass. Recorded "
                  "as not evidenced rather than assumed.")),
    absent(s, "smart_meter_required", "Whether a smart meter is required."),
    absent(s, "deemed_export_treatment",
           "Whether export is paid where the home cannot have a smart meter."),
    absent(s, "customer_of_supplier_required",
           "Whether only the supplier's own customers are eligible.",
           notes="A 'Can you sign with Flogas for an export tariff only?' "
                 "section exists but was not captured."),
    absent(s, "caps_minimum_terms_exclusions",
           "Published caps, minimum terms or exclusions."),
]


def derive_state(c):
    et = c["evidence_type"]
    if et == "ABSENCE_OF_RECORD":
        return "NOT_PUBLICLY_EVIDENCED"
    if et == "UNTESTED":
        return "UNKNOWN"
    if et == "CONFLICTING_SOURCES":
        return "CONTRADICTED"
    if c["provenance"] == "COMMERCIAL_CORRESPONDENCE" or et == "CORRESPONDENCE":
        return "SUPPLIER-CLAIMED"
    # Every published supplier commercial term is the supplier asserting its own
    # proposition. Unlike a statutory instrument or a contract a homeowner has
    # signed, nothing independent confirms it — so it is SUPPLIER-CLAIMED, not
    # VERIFIED, however precisely it is published.
    return "SUPPLIER-CLAIMED"


def comparable_rates(*_args, **_kw):
    """THE VAT FIREWALL, IN ONE PLACE, AS A REFUSAL.

    There is deliberately no ranking, normalisation, "best rate" or derived
    annual-earnings function in this file. Three of the four pilot suppliers
    publish a rate with no VAT basis; the VAT adjustment (~1.7c at 9%) exceeds
    the spread between suppliers (~1c), so any ordering built on the published
    figures could place them in the wrong order.

    This function exists so that the refusal is explicit and testable rather
    than merely absent.
    """
    raise NotImplementedError(
        "Rate comparison is forbidden while VAT basis is UNKNOWN for any pilot "
        "supplier. Compare structural conditions — smart meter required, deemed "
        "export supported, customer-of-supplier required, payment mechanism and "
        "frequency — not rates."
    )


def resolve(as_of, c):
    lv = datetime.strptime(c["last_verified"], "%Y-%m-%d").date()
    months = (as_of.year - lv.year) * 12 + (as_of.month - lv.month)
    if as_of.day < lv.day:
        months -= 1
    due = months >= c["review_interval_months"]
    out = dict(c)
    out["evidence_state_derived"] = derive_state(c)
    out["months_since_verified"] = max(months, 0)
    out["verification_status"] = "STALE" if due else "CURRENT"
    out["logic_safe_resolved"] = (
        bool(c["logic_safe"]) and not due
        and c["evidence_type"] not in NEVER_LOGIC_SAFE_TYPES
        and c["provenance"] != "COMMERCIAL_CORRESPONDENCE")
    out["homeowner_safe_resolved"] = (
        bool(c["homeowner_safe"]) and not due
        and c["provenance"] != "COMMERCIAL_CORRESPONDENCE")
    return out


def build(as_of):
    claims = [resolve(as_of, c) for c in C]

    def tally(key):
        t = {}
        for c in claims:
            t[c[key]] = t.get(c[key], 0) + 1
        return t

    per_supplier = {}
    for k, v in SUPPLIERS.items():
        mine = [c for c in claims if c["supplier_key"] == k]
        vat = next((c for c in mine if c["claim_field"] == "export_rate_vat_basis"), None)
        per_supplier[k] = {
            "supplier_name": v["supplier_name"],
            "atlas_organisation_code": v["atlas_organisation_code"],
            "selected_because": v["selected_because"],
            "claimCount": len(mine),
            "vatBasisEstablished": bool(vat and vat["evidence_type"] == "PUBLISHED_SOURCE"),
        }

    return {
        "schema": SCHEMA,
        "generated": as_of.isoformat(),
        "jurisdiction": JURISDICTION,
        "pilot": True,
        "pilotNote": PILOT_NOTE,
        "rulesManifest": (
            "National rules (SEAI grant, CRU export obligation, ESB Networks "
            "requirements, tax, VAT, planning) remain governed solely by "
            "plotnua.disc026.evidence.v1. This manifest restates none of them "
            "and holds only what varies by supplier."
        ),
        "canonicalModel": (
            "PlotNua evidence-manifest decomposition plus claim_basis. "
            "evidence_state_derived is a DISPLAY LABEL computed from the "
            "dimensions; it is never stored truth and never hand-set."
        ),
        "comparisonGovernance": {
            "rateComparison": "FORBIDDEN",
            "reason": (
                "Only 1 of 4 pilot suppliers publishes a VAT basis. The VAT "
                "adjustment (~1.7c at 9%) exceeds the spread between suppliers "
                "(~1c), so ranking on published figures could order them "
                "wrongly."
            ),
            "permittedComparison": [
                "smart meter required?", "deemed export supported?",
                "must I be that supplier's customer?",
                "how is the benefit credited or paid?", "how frequently?",
                "what rate does the supplier currently publish, on its own stated basis?",
                "what material information remains UNKNOWN?",
            ],
            "notALeagueTable": (
                "Supplier selection is evidence-shaped. It must never be "
                "presented as best, cheapest or recommended suppliers."
            ),
        },
        "imageRights": {
            "supplierImagesUsed": 0, "logosUsed": 0, "hotlinks": 0,
            "assetRecordsCreated": 0,
            "note": "This pilot deliberately proves Atlas value with zero third-party imagery.",
        },
        "supplierCount": len(SUPPLIERS),
        "suppliers": per_supplier,
        "claimCount": len(claims),
        "claimsByBasis": tally("claim_basis"),
        "claimsByEvidenceType": tally("evidence_type"),
        "claimsByDerivedState": tally("evidence_state_derived"),
        "claimsByProvenance": tally("provenance"),
        "homeownerSafeCount": sum(1 for c in claims if c["homeowner_safe_resolved"]),
        "logicSafeCount": sum(1 for c in claims if c["logic_safe_resolved"]),
        "note": (
            "Generated by .github/scripts/generate_supplier_export_evidence.py. "
            "Do not hand-edit. Staleness resolved at generation time. NOT "
            "homeowner-facing, NOT wired to the DISC-026 journey, NOT deployed. "
            "No Atlas Product, Technology or Programme record was created."
        ),
        "claims": claims,
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="supplier-export-evidence.json")
    ap.add_argument("--as-of", default=None)
    a = ap.parse_args()
    as_of = (datetime.strptime(a.as_of, "%Y-%m-%d").date() if a.as_of else date.today())

    for c in C:
        for field, allowed in (("claim_basis", CLAIM_BASIS),
                               ("evidence_type", EVIDENCE_TYPE),
                               ("source_type", SOURCE_TYPE),
                               ("provenance", PROVENANCE),
                               ("maturity", MATURITY)):
            if c[field] not in allowed:
                print(f"FAIL {c['claim_key']}: bad {field}={c[field]!r}", file=sys.stderr)
                return 1
        if c["claim_basis"] != "STATED":
            print(f"FAIL {c['claim_key']}: only STATED is permitted", file=sys.stderr)
            return 1

    p = build(as_of)
    Path(a.out).write_text(json.dumps(p, indent=2, ensure_ascii=False) + "\n",
                           encoding="utf-8")
    print(f"  wrote {a.out}   schema {SCHEMA}")
    print(f"  suppliers {p['supplierCount']}  claims {p['claimCount']}")
    print(f"    basis          {p['claimsByBasis']}")
    print(f"    derived state  {p['claimsByDerivedState']}")
    print(f"    evidence type  {p['claimsByEvidenceType']}")
    print(f"  homeowner-safe {p['homeownerSafeCount']}  logic-safe {p['logicSafeCount']}")
    print(f"  VAT basis established: "
          f"{[k for k,v in p['suppliers'].items() if v['vatBasisEstablished']]}")
    print(f"  rate comparison: {p['comparisonGovernance']['rateComparison']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
