
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

## BB-CFG-003 · The acquisition contract had not kept up with the price contract
Opened and CLOSED 11 October 2026.

`additional_home_qualification._configuration_of()` reads a pricing field
called `Configuration`. `PRICING_FIELDS` in `snapshot_atlas.py` never asked
for it, because that list predates the named-configuration price contract.
Airtable returns only the fields requested, so a fresh snapshot would have
carried no Configuration at all.

Measured through the real functions against the live BIOBUILDS rows:

```
with Configuration     VERIFIED_NUMERIC_PRICE  EUR 105,000 / 163,000, both
                       labelled, INCLUDES_VAT, three commercial terms
without it             PRICE_AMBIGUOUS_MULTI_ROW, amount None
```

Wanderlust would have regenerated as a held product with no published price.
Nothing would have crashed and no guard then in place would have objected.

Closed by `build-snapshot-configuration-field.py`: the field is requested, and
`configuration_problems()` refuses a snapshot in which an Additional Home
product carries more than one numeric price and no labels. Deliberately NOT a
blanket required field — only BIOBUILDS populates it today, so requiring it
everywhere would fail unrelated snapshots for an absence that is usually
correct. Proved by `prove-snapshot-configuration.py`, 9/9.

THE GENERAL LESSON, worth more than the fix: a reader that learns to use a new
field does not teach the acquisition layer to fetch it. Every future field the
qualification code starts reading needs the same one-line addition, and the
same question asked of it.

## BB-CFG-004 · Two new guards are not yet in CI
Opened 11 October 2026.

`prove-snapshot-configuration.py` is safe to run in CI today — no artefact
dependency, no token. `verify-biobuilds-publication.mjs` is not: it checks a
REGENERATED `additional-home-universe-v1.json`, and would fail against the
artefact currently committed, correctly, because that artefact predates the
regeneration. Wire the first now and the second immediately after the
regenerated universe is committed. A guard outside CI rots.

## GR-SAN-001 · test_qualification_batch1 has three pre-existing failures
Opened 11 October 2026. NOT caused by, and not related to, the BIOBUILDS work.

Measured at HEAD before any change in this session, and again after: identical.

```
the 8 governed-zero placeholder records are corrected    0 corrected
sanitiser removes at least 95% of leaking strings        8 -> 8
useful sentences behind an internal label are kept       label removed
```

These test the GARDEN ROOM universe, which has not been regenerated since the
sanitiser work landed. The test is measuring a stale artefact, not a broken
sanitiser — but that is a claim to verify, not to assume, and it needs a
Garden Room regeneration to settle either way.

## BB-NEST-001 · Nest 24's Irish prices cannot be re-verified first-party
Opened 11 October 2026. **OUTSTANDING.** Founder decision: Option A — the
configuration labels were applied and the deployment resumed; this was left
deliberately open rather than fixed in passing.

The two Nest 24 Pricing records (PROD-001172) cite
`biobuilds.com/ie/design#nest-24`, verified by a curator on 28 September 2026:
EUR 101,100 incl. VAT Turnkey and EUR 74,300 incl. VAT Exterior Finished.

Checked 11 October 2026:

- `biobuilds.com/ie/design` publishes FOUR models — Wanderlust, Serenity,
  Sanctuary, Bloom — with anchors `#wanderlust-48`, `#serenity-95`,
  `#sanctuary-142`, `#bloom-190`. There is no Nest, and no `#nest-24`.
- `biobuilds.com/design` (EU) publishes the same four. No Nest.
- Nest is nonetheless a real BIOBUILDS model: a 24 m² unit referenced on the
  company's blog, FAQ, catalog and turnkey pages, with a blog figure of "From
  EUR 62,200" net of VAT — which the Atlas record itself notes as the EU price.
  It appears withdrawn from, or never carried on, the configurators now serving
  Ireland and the EU.
- The 28 September capture has drifted on what CAN still be compared: the
  record lists options at smart blinds EUR 2,500, Zehnder EUR 6,000, solar
  EUR 9,800. The live Irish page today lists EUR 5,000, EUR 9,500, EUR 14,500.

WHAT IS AT RISK, EXACTLY. Both prices sit in the artefact marked `Verified`
with `Evidence Scope = Product-Specific`, and that word is load-bearing
everywhere else in Atlas. Nest 24 reaches no homeowner surface today — it has
no feature values, so no usable area, so Class 3A `no-usable-area`, the same
containment as Serenity; and it has no approved imagery, the BIOBUILDS grant
enumerating three assets for PROD-000523 and three for PROD-000524 and none
for PROD-001172. So this is a governance debt, not a homeowner-facing
falsehood. It becomes one the moment an area is recorded for Nest 24, or any
new surface reads Additional Home prices without the Class 3A gate.

THE REMEDY, when it is picked up:
  1. Establish whether Nest is purchasable in Ireland at all. The supplier is
     the only authority on this; a contact already exists via the BIOBUILDS
     correspondence register.
  2. If it is not, the two prices should stop being `Verified` and the product
     should say what is true: a model Atlas recorded once, with no current
     published Irish route.
  3. If it is, re-verify both figures and the option prices, and update
     `Last Price Check`.
  4. Do NOT read 24 m² from the model name. BIOBUILDS' naming is a
     configurator key, not a measurement: "Wanderlust 48" has a published
     interior of 35.54 m², and "Serenity 95" has 77.06-78.21 m².

WHAT THE LABELS DID AND DID NOT SETTLE. Setting Configuration describes what
the supplier published, which is true of the 28 September capture whatever its
availability now. It says nothing about whether the price is still buyable.
Those are two different questions and only the first has been answered.

THE WIDER LESSON. The guard that caught this was written to prevent a product
publishing with no price. It found a stale capture instead — because a product
nobody had looked at since intake was the one with the missing field. Worth
remembering when the next guard seems to be objecting to a technicality.
