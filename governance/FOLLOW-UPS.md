
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
