
## BB-AIR-001 · BIOBUILDS prices in the Atlas universe (opened 11 October 2026)

`additional-home-universe-v1.json` still carries the superseded BIOBUILDS
amounts:

    PROD-000523  BIOBUILDS Wanderlust  amount 112700.0  EUR  Starting From
    PROD-000524  BIOBUILDS Serenity    amount 208500.0  EUR  Starting From

Correct values, confirmed first-party at biobuilds.com on 11 October 2026:

    Wanderlust  €105,000 exterior finished   €163,000 turnkey   (incl. 23% VAT)
    Serenity    €191,000 exterior finished   €306,000 turnkey   (incl. 23% VAT)

Two reasons this was NOT patched locally with the preview correction:

1. The file is generated from Airtable by
   `.github/scripts/generate_additional_home_universe.py`. A local edit is
   overwritten on the next refresh, so the correction has to be made in
   Airtable.
2. The schema carries a single `amount` per product. It cannot represent the
   two-finish model BIOBUILDS now publishes. Choosing which figure to store,
   or widening the schema, is a pricing-architecture decision, not a supplier
   correction.

Not urgent and not public: `prove-biobuilds-containment.mjs` confirms neither
product is reachable from any runtime payload or the public journey, so no
homeowner can see either figure today.

Needs: (a) the Airtable correction, (b) a decision on how the universe schema
carries exterior-finished vs turnkey.

### BB-AIR-001 — CLOSED, 11 October 2026

The Airtable corrections are done. Record of exactly what changed:

SCHEMA, one field
  Pricing.Configuration  fldp4puJm09VbGYR6  singleSelect
  Exterior Finished | Turnkey | Basic | Optima. Empty behaves as before, so
  every other product in the base is unaffected.

PRICING, 6 updated + 2 created
  recrgrc4uTUEdi4Uw  Liora Basic    EUR 28,070   + Basic,  VAT -> Excluding VAT
  recHTBl9gKdLuFp6O  Liora Optima   EUR 32,830   + Optima, VAT -> Excluding VAT
  recvrcwzN1ngzmZzN  Baby Basic     EUR 25,533   + Basic,  VAT -> Excluding VAT
  recamJZHHCPSnm3p6  Baby Optima    EUR 29,103   + Optima, VAT -> Excluding VAT
  reccFXgzN2N6KepuW  Wanderlust     112,700 -> 105,000, Exterior Finished, VAT Yes
  recTQrnCzBN4irZ6E  Serenity       208,500 -> 191,000, Exterior Finished, VAT Yes
  recnHZrHnYPG494XW  Wanderlust     EUR 163,000  NEW, Turnkey, VAT Yes
  recrCqAw0NIPNxobb  Serenity       EUR 306,000  NEW, Turnkey, VAT Yes

The four Tiny House Heavens VAT corrections were not cosmetic. Each row said
"Price Includes VAT = Yes" while its own Known Exclusions note said "Price
stated exclusive of VAT (+VAT) - CONFIRMED (not inferred)". The note was
right and the field was wrong.

PRODUCTS, 2 descriptions rewritten
  recIBexeX8au55mVn / reczLG8Iw4k7TY2Nq. Superseded prices removed, both
  configurations stated with VAT basis and exclusions, and the five claims
  carried over from the August catalogue read (Passivhaus certification,
  0.4 ACH@50, 15 kWh/m2/yr, carbon-negative EPD, 3-week move-in) are now
  explicitly labelled AWAITING RE-VERIFICATION rather than stated as fact.
  Wanderlust's description records that "48" is a model name, not an area.

CLOSED 11 October 2026 -- THIS ENTRY WAS STALE
  Wanderlust interior area 35.54 m2 as a FeatureValue. Recorded here as still
  open; it is not. Verified against the live base on 11 October 2026:
  FeatureValues receQnVnj37Zfnv5o carries Value Number
  35.54, Unit m2, Evidence Scope Product-Specific, Status Verified, against
  Feature Internal Floor Area (rechP7fg3NRe4bWXD) on BIOBUILDS Wanderlust
  (recIBexeX8au55mVn). Its Value Text records the 48-in-the-model-name
  distinction. The write had already been made; this note had not been
  updated. Driving the real _area_evidence() and class_3a() over that record
  returns area=35.54, basis=VERIFIED_INTERNAL, class3a=CANDIDATE.

---

## BB-CFG-001 · The Garden Room VAT basis is held but not shown
Opened 11 October 2026, with the Results and Compare configuration readers.

The Additional Home price now carries its governed VAT basis to the homeowner,
because two of the suppliers publishing named configurations publish them on
OPPOSITE bases — BIOBUILDS including 23% VAT, Tiny House Heavens excluding it —
and at that rate the basis is not a footnote.

The Garden Room pathway holds the same fact under a different name and a
different vocabulary: `priceEvidence.includesVat`, valued Yes / No / Unknown,
against the Additional Home `basis` token INCLUDES_VAT / EXCLUDES_VAT /
VAT_UNKNOWN. The price presentation reads `basis` only, so a Garden Room price
renders with no VAT note — exactly as it did before this change, and as
prove-price-presentation-unchanged.mjs asserts across all 573.

NOT DONE HERE, DELIBERATELY. Surfacing it would be a homeowner-copy change
across 573 products, and it cannot be done from the field alone: the C1
reconciliation measured a systemic contradiction in these records, where a
"Yes" is contradicted by the record's own evidence note. Publishing "including
VAT" off a field that is wrong 6 times in 19 would be worse than publishing
nothing. The order is: reconcile the records, then surface the basis.

WHAT IT WOULD TAKE
  1. Reconcile `Price Includes VAT` against each record's own evidence note
     for the Garden Room pricing rows, correcting where the evidence is clear
     and leaving Unknown where it is not.
  2. Map includesVat -> the basis token in the Garden Room generator, so there
     is one vocabulary rather than two.
  3. The reader needs no change: pnVatBasis() already reads the token, and
     PC6-PC8 already assert the three outcomes.

## BB-CFG-002 · The commercial-term vocabulary is four tokens wide
Opened 11 October 2026.

COMMERCIAL_TERM_ANCHORS recognises exactly four terms, written against the
eight pricing rows that carry a Configuration — measured from the live base on
11 October 2026. It fails in the honest direction: wording the anchors do not
match produces no token and the term is simply not stated, and nothing
anywhere renders an absent term as an inclusion.

So a supplier added later whose evidence words these same facts differently
will show no commercial terms at all. That is safe but thin, and the remedy is
not a looser anchor — C-C15 in the capability proof demonstrates what a
loosened anchor does. The remedy is to read the new wording and add a token,
or to govern the terms as a field rather than recognise them in prose.
