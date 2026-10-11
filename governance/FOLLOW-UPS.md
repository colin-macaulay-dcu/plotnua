
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

STILL OPEN
  Wanderlust interior area 35.54 m2 as a FeatureValue. Deliberately last.
  The gate now holds BIOBUILDS regardless of area (PG6, PG11, PG12), so this
  is no longer the publication trigger it was -- but it is the one write that
  used to be, and it is better done deliberately than at the end of a long
  session. One write, then regenerate.
