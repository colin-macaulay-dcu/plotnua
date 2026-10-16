# Supplier tiers: Publishable Supplier and Gold Standard

**Founder decision:** 16 Oct 2026 ("PLOTNUA — FOUNDER AUTHORISATION: EXECUTE NOW", section 7).

## Tier 1: Publishable Supplier (the publication standard)

A supplier's products may appear in public journeys when all of these hold:

1. **Written permission** from the supplier's own domain, founder-confirmed (Image Permission Outreach plus `image-rights-records.json`).
2. **Identity:** the supplier's own website, contact details and locality.
3. **Irish route:** delivery or installation in the Republic of Ireland is evidenced, or clearly caveated on the listing.
4. **No unresolved recorded contradiction** on the product.

Each product must also pass its journey's own qualification rules, the image-rights gate and the publication gate.

## Tier 2: Gold Standard (optional badge)

Gold Standard is Tier 1 plus, from accessible primary evidence:

- the legal entity;
- its company registration;
- an explicit link between the trading name and that entity;
- formal warranty documentation.

**It is never a condition for ordinary discovery.** "Atlas Certification Audit v1" and "Results Eligibility v1" measure progress towards Tier 2 only. No site code reads them.

Existing evidence, statuses and audit history are preserved unchanged. The table descriptions on Products and Organisations record this decision (written 16 Oct 2026).

## Certification formula fix: manual schema step

The Airtable API cannot create formula or count fields. Do this in the Airtable UI, Products table:

1. **Add three Count fields:**

   | Field name | Counts |
   |---|---|
   | `Count FV` | Product Feature Values |
   | `Count Pricing` | Product Pricing |
   | `Count Availability` | Product Availability |

2. **Replace the formula** of "Atlas Product Certification Audit v1" (fldRJ8mb6hU51ciGr) with:

```
IF(FIND("GOLD STANDARD — VERIFIED",UPPER({Standards}&"")),"Atlas Gold Standard Product",
IF(FIND("BLOCKED",UPPER({Standards}&"")),"Blocked — Recorded Contradiction or Certification Gate",
IF(OR({Organisation}=BLANK(),{Product URL}=BLANK(),{Sources}=BLANK()),"Blocked — Core Attribution or Evidence Missing",
IF(AND({Count FV}>0,{Count Pricing}>0,{Count Availability}>0),"Tier 1 Evidence Complete — Publishable (Gold Standard optional)",
"In Progress — Product Intelligence Gaps"))))
```

**What changes:**

- Only the evidence test (`!=BLANK()` becomes `>0` on counts) and the wording of the complete state.
- The defect that let 636 of the 908 "Evidence Complete" products pass without links is closed.
- No record values are edited. The formula is derived, so audit history is unaffected.
