
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

## AH-STAT-001 · Two Additional Home products carry no Product Code
Opened 11 October 2026. The CRASH is fixed; the DATA GAP is outstanding.

The Stage 3 generator failure was a code defect and has been corrected. What
caused it to fire, though, is an Atlas gap that is still there:

```
recFek9ErsnKt6uKN   Yardbox Aspect Modular Homes
recPermX1OwzI2o1Y   Yardbox Bothán
```

Both created 2026-09-29, both Product Category = Additional Home, both with
NO Product Code and NO Habitation Classification. `Product Code` is requested
by the snapshot but is not in REQUIRED_PRODUCT_FIELDS, so an uncoded product
is a legal snapshot and always was.

They now appear in the regenerated artefact as `categoryWithoutConfirmedUncoded`,
which is the point of that key: the gap is stated rather than inferred from a
null. Downstream they are inert — habitation `UNKNOWN / NOT YET ASSESSED`, so
Class 3A `habitation-not-confirmed`; no price published; no imagery.

THE REMEDY is curation, not code: mint Product Codes for both, and assess
habitation. Until then they sit in the category contributing nothing, which is
exactly what the statistic is for.

WORTH NOTING for the next intake. These two were created the day after the
Nest 24 records, in the same week, and carry the same signature: a product
added to a category before its identifying and classifying fields were filled
in. Two separate deployment stops have now traced back to that one week of
intakes. A pre-flight that lists Additional Home products missing a code or a
habitation classification would have surfaced both before either stopped a
deployment.

## MYCABIN-DESC-001 · The Description field holds a research dossier
Opened 11 October 2026. **OUTSTANDING, and it is the bigger half of this.**

The firewall stop was caused by one sentence. Fixing that sentence does not
fix what it was sitting inside.

The MyCabin intake of 28 September wrote a full curator's dossier into the
Airtable **Description** field — the field the generator publishes — rather
than into Notes. What now reaches `.description` for PROD-001194 includes:

```
SKU: ONE BED D 4070-44. WooCommerce product ID 31299, type simple.
*** AREA IS PUBLISHED - ONE OF ONLY TWO PRODUCTS IN THE RANGE. ***
MEASUREMENT BASIS: INTERNAL, STATED BY THE SUPPLIER.
SUPPLIER DATA DEFECT - RECORDED, NOT CORRECTED:
DEFECT 1 - LOG THICKNESS: spec table 45mm vs WooCommerce attribute 44mm.
UNKNOWN remains UNKNOWN. NOTHING WAS INFERRED.
```

None of that is homeowner-facing copy. It is good research in the wrong field.

WHY IT IS NOT FIXED HERE. The lead-phrase rule in `homeowner_text()` is a
CLOSED vocabulary, and the labels in this dossier — SKU, PRICE, DIMENSIONS,
CONSTRUCTION, WARRANTY, SHOWROOMS, PROPOSITION — are not internal markers.
Several carry real homeowner value: warranty duration, dimensions, insulation
build-up. Adding them all to the closed list would delete genuine evidence
across 701 products to tidy two records, which is exactly the trade the
function's own docstring warns against. That is a curation decision and a
measurement exercise, not a line of regex, and it is the founder's call.

CONTAINMENT TODAY. Both products are Class 3A `NOT_A_CANDIDATE`, so neither
reaches Results. The descriptions sit in the artefact and would be shown by
any surface that reads `.description` for an Additional Home product.

THE REMEDY, in order of preference:
  1. Move the dossier to Notes and write a short Description, in Airtable, by
     a curator. No code change, and it fixes the class.
  2. Failing that, extend the lead-phrase vocabulary — but only after
     measuring, per label, how many of the 701 products would lose text and
     what that text is.

NOT A REASON TO DELAY THE BIOBUILDS DEPLOYMENT. The authorised release is
Wanderlux and Serenity; these two MyCabin products reach no homeowner surface.
But the next intake review should start here.

## FW-PROP-001 · The property-assertion pattern is narrower than its name
Opened 11 October 2026. Recorded, deliberately not widened.

`PROPERTY_CLAIM_RE` matches `your (property|site|garden) (is|qualifies)`, so it
caught `If your site is long and narrow` on PROD-001194 and PROD-001201. It
does NOT catch the sibling record's siting sentence on PROD-001193:

```
SITING: "With a width of 7m and a depth of just 4m, it maximizes the room
inside WITHOUT OVERTAKING YOUR GARDEN."
```

That is second-person language about the homeowner's garden, and it is still
published. It makes no claim about what the garden IS, so it is a weaker case
than the two that were caught — but it is the same family.

Widening the pattern is a one-line change and a universe-wide blast radius, so
it is recorded rather than done. If it is widened, re-run the pre/post
comparison across all 701 products x 3 text fields, which is the measurement
that made this fix safe: 0 outputs changed.

## PG7-MIG-001 · The VAT-basis migration branch is retired
Opened and CLOSED 11 October 2026.

`prove-supplier-publication-gate-capability.mjs` reported C-PG7 BLIND after
the founder's regeneration. Measured against the regenerated artefact:

```
priced products            125
of those WITHOUT basis       0
C-PG7 as written        sets basis = 'INCLUDES_VAT' on the first priced
                        product -> the artefact was BYTE-IDENTICAL after
                        the mutation. A no-op cannot be caught.
```

Before the regeneration no priced product had a basis, so setting one broke
the uniformity PG7's migration branch excused, and PG7 reported it. After the
regeneration every priced product already holds that exact value. The mutation
aged out the moment the migration completed.

TWO HALVES, ONE ROOT CAUSE — the migration finished and two things still
assumed it had not:

| | PG7 before | PG7 after |
|---|---|---|
| unmutated | PASS 125 priced | PASS 125 priced |
| old mutation (set basis) | PASS | PASS |
| new mutation (delete one basis) | REFUSE 1 of 125 | REFUSE 1 of 125 |
| stress (delete ALL bases) | **PASS — migration branch** | REFUSE 125 of 125 |

Row three says the mutation re-aim restores 14/14 on its own. Row four is why
the branch had to go: a generator regression that stripped VAT basis from all
125 priced products would have been reported "ok, not yet regenerated" — the
guard excusing exactly what it exists to forbid.

THE GENERAL LESSON, worth more than the fix. A guard written with a
"not yet migrated" branch carries an expiry date that nothing enforces. The
branch was honest when written and became a hole the day the migration
completed, and the only reason it surfaced is that a mutation aimed at it went
BLIND. Any future transitional branch should name the condition that retires
it, so the guard fails rather than excuses once that condition is met.

NOT A WEAKENING. The branch retirement removes an excuse; it adds none. PG7
keeps its headline assertion, its vacuous arm and its pass arm. All 14
mutations are caught by their owning guard, and the proof confirms the real
tree was untouched.

## GR-CHECK-001 · Garden Retreat has no property assessment (opened 14 October 2026)

A FUTURE DEVELOPMENT, recorded by founder instruction ("Garden Retreat — final
pre-launch corrections", item 5). It is NOT built and must not be implied.

The intended journey is Discovery → Check → Result → Makers. Today it stops at
Makers:

- **Check — missing.** `your-plot.html` holds DISCOVERY_CONTENT for
  garden-room and residential only. There is no Garden Retreat question set,
  and Cluster 2 guard E1 forbids a `?discovery=` route from this page.
- **Result — missing.** No wellness matching exists. Nothing reads
  `wellness-universe-v1.json` except the maker explorer and Search.
- **Makers — live.** The explorer lists the public wellness products by kind.

What the page says instead: the hero offers no "Check your garden" action;
"Could it work for your property?" says PlotNua does not yet have a property
check for garden retreats and that nothing on the page assesses a property;
the shared Property Brain panel says the check is being prepared and is not
ready. `build-garden-retreat-restructure.py` GR2 refuses a "Check your
garden" action in the hero.

Needs, before anything is built: a founder-approved scope for the questions
(clear space and where it is, power and water routes, ground, existing
structures and the 30 m² allowance), a decision on whether results match
products or only explain feasibility, and an amendment to Cluster 2 E1 if a
route from this page is wanted.

## WL-HOLD-001 · 118 held wellness products: what holds each (opened 14 October 2026)

Founder brief "Garden Retreat — final pre-launch corrections", item 2. Of 153
Atlas Wellness / Sauna products from 11 organisations, 35 from 3 makers are
public (OGNYX 29, Tanktribe 4, Irish Sauna Company 2). The other 118:

| Class | What holds them | Products |
|---|---|---|
| A · evidence | OGNYX 12 (their own pages contradict themselves; Standards BLOCKED); TimberIN 2 (no verified price); Auroom Wellness 2 (no verified price, type unclassified) | 16 |
| B · image rights alone | none. Text listing does not need images. MyCabin declined image permission (17 Sep 2026), which bars its imagery; its text is held under C | 0 |
| C · no permission record, factual evidence otherwise sufficient | Pineca Ireland 35, Hansa24 Group (Gardenhouse24) 27, Polaris Sauna 20, MyCabin.ie 12, TimberIN 6, Sommarnöjen 1 | 101 |
| D · another established rule | Cosy Cabins 1 (asked for a preview first: §10.1, publication stays blocked until it answers). Auroom Wellness is also preview-only and never searchable (counted under A) | 1 |

WHY C IS NOT PUBLISHED. The wellness universe uses the supplier publication
gate (founder decision, OGNYX integration, 14 Oct 2026). The gate fails closed:
an organisation with no rights record derives `publication-record-missing`,
which is NEVER_WAIVABLE, and the legacy baseline that grandfathers older
Additional Home listings "may only shrink" and was never extended to wellness.
So the existing rules do not clearly permit a text-only listing without a
permission record, and none was added.

THE PRECEDENT THAT POINTS THE OTHER WAY. The garden-room universe has no gate
and publishes factual text listings for 64 organisations without supplier
approval; MyCabin.ie, Pineca Ireland, Hansa24 Group and Cosy Cabins are among
them on Living in the Garden today. The founder's standing rule that a
supplier's participation or image decision must not affect Atlas's factual
assessment supports text-only listing; the 14 Oct gate decision does not.

DECISION REQUIRED (not taken here): whether gated universes may carry a
text-only "public information" listing — e.g. a recorded permission state
meaning "no imagery, factual listing from the maker's own public pages" —
without supplier approval. If yes, the gate needs that state defined, the 101
products in C would follow at the next regeneration, and MyCabin's decline
would still bar its images.

## OOD-IMG-001 · One authorised ÖÖD Extended House file held (14 Oct 2026)

The ÖÖD House targeted update publishes 28 of the 41 per-file scoped ÖÖD
photographs, each on the model its folder in ÖÖD's library names (Atlas Assets
records created 14 Oct 2026; `apply_authorised_imagery.py` ATLAS_ASSETS). The
12 sauna photographs have no Atlas product. Extended House file
`126bHQPCLpLoZE2C7qddQ-v__3gR85Hmg` ("Extended House.jpg") is held: it may be
a computer rendering and nothing records which, and a visualisation must never
be shown as a photograph. To use it, establish the medium (ask ÖÖD only when
other correspondence is needed — not on its own), then add one ATLAS_ASSETS
entry with an Atlas Asset record. No other change is needed.

## JC2-CREDIT-001 · Option Detail removed every photograph credit (fixed 14 Oct 2026)

`your-plot.html` Option Detail attached the governed credit chip and then, later
in the same function, cleared "the previous product's" chip — removing the one
just attached. Every governed photograph on Option Detail (Powersheds, Yard
Box, and now ÖÖD) showed without its required credit. The clear now runs
before the paint. Found by browser test of the ÖÖD update. A proof that
asserts a credit chip is present after Option Detail opens would stop a
regression; none exists yet.

## WL-HOLD-001 · RESOLVED IN PART, 14 Oct 2026 (controlled text-only publication)

Founder decision: a factual, text-only listing basis
(`atlas-tools/public-information-listings.json`), never a permission, never
imagery; a rights record always decides first. Garden Retreat now lists 120
products from 7 makers: 35 on supplier permission (OGNYX 29, Tanktribe 4,
Irish Sauna Company 2) and 85 on the public-information basis (Pineca 34,
Hansa24 25, Polaris 20, TimberIN 6), each with a VERIFIED product page
(`atlas-tools/maker-product-links-v1.json`). Still held (33): OGNYX 12
(recorded contradictions), MyCabin 12 (10 pending founder review + 2
contradictions), Pineca ELDA 5 m², Hansa Geira and Nord (contradictions,
written to Atlas Standards 14 Oct), TimberIN 2 (no verified price), Auroom 2,
Cosy Cabins 1 (asked for a preview first), Sommarnöjen 1 (page 404).

OPEN:
* SEARCH-WL-COLLIDE · RESOLVED 14 Oct 2026 (founder: FIX). Search now decides
  wellness eligibility per product; the supplier record of a maker in both
  corpora counts both (R3 holds). Index 175.0 KB of the 180 KB G10 guard:
  about 5 KB of headroom left. Original note: 59 of the 85 (Pineca 34, Hansa24 25) are in the
  Garden Retreat directory but NOT in Search: build-search-index.py withholds
  wellness products of an organisation that already has a Garden Room
  supplier record (R3: a supplier control must deliver exactly the count it
  promises). Lifting it means letting supplier records span corpora — a
  founder decision, not taken here.
* MYCABIN-EDITORIAL · RESOLVED 14 Oct 2026: the sauna example is now Hansa24's
  Lisette (G0093); GR10 refuses any held maker's name on the page. Original
  note: Garden Retreat's comparison section names MyCabin's
  Cube Sauna M with its price and showrooms (editorial since September).
  MyCabin replied "This is not something we are interested in" (17 Sep).
  The directory holds MyCabin; the editorial does not. Founder to decide.
* COSY-CLUSTER1 · RESOLVED 14 Oct 2026: the figure is the 7 October research
  snapshot (B); the page now says so, with the date derived from the evidence
  file's own stamp. Original note: Living in the Garden's cost section still says "out of 573
  garden-room records" (frozen Cluster 1 evidence, 7 Oct); the universe is now
  572 after the Cosy Cabins hold. Refresh that evidence at the next Cluster 1
  update.
