# PHASE 6A · ATLAS WRITE LEDGER
**Applied 6 October 2026. Every row below was re-read from live Atlas after the write.**
Base appoLZFWesvoPhZGR · Product Pricing tblqsjmkTrwSct7gv · Products tblMiUcO4OT9ia2aE · Organisations tblngwmviAcWxFKsW

## APPLIED — 12 records

| # | record | product | field | old | new | evidence | post-write |
|---|---|---|---|---|---|---|---|
| A1 | **recmhqpPfdjlXEia2** (created) | CUBE Garden Room Range recfFcnNP9ZV4BcVW | Base/From, To, Cur, Type, Status, Scope, VAT, LPC | — | 36500 / 36500 / 47850 / EUR / Starting From / Verified / Product-Specific / Yes / 2026-10-06 | gardenrooms.ie/designs/cube-range/ 2026-10-06 (page modified 2026-09-30) | VERIFIED |
| A2 | **recPZnwHVecuaGX88** (created) | Ultimate Garden Room Range recnBe46LKTCzLJ3P | as above | — | 43650 / 43650 / 53650 / EUR / Starting From / Verified / Product-Specific / Yes / 2026-10-06 | gardenrooms.ie/designs/ultimate-range/ 2026-10-06 | VERIFIED |
| B1 | recoP4v6gYk8wQ9uS | Shomera Contemporary Range | Base Price | 35950 | **36450** | shomera.ie/garden-rooms/ 2026-10-06 | VERIFIED |
| B1 | recoP4v6gYk8wQ9uS | Shomera Contemporary Range | Price To | *(empty)* | **46950** | same | VERIFIED |
| B2 | recDiJX5C1S3DbbUo | Shomera Classic Range | Price To | *(empty)* | **44950** | same | VERIFIED |
| E1 | recVzYsqCkxq61nmE | Big Man Deluxe Home Office | Price From | 60000 | **(cleared)** | own note + first-party absence | VERIFIED |
| E1 | recVzYsqCkxq61nmE | Big Man Deluxe Home Office | Price To | 70000 | **(cleared)** | same | VERIFIED |
| E1 | recVzYsqCkxq61nmE | Big Man Deluxe Home Office | Status | Partially Verified | **Archived** | same | VERIFIED |
| F1 | recRrxTAURDOmxjW6 | Loghouse ECO 6.0×4.0 | Price To | *(empty)* | **36420** | loghouse.ie product + category, 2026-10-06 | VERIFIED |
| F2 | recThHwTwhFjnqgCw | Loghouse ECO 4.0×3.0 | Price To | *(empty)* | **22920** | loghouse.ie category 2026-10-06 | VERIFIED |
| F3 | recUhaluaReaTxSLQ | Loghouse ECO 4.0×4.0 | Price To | *(empty)* | **27090** | same | VERIFIED |
| F4 | recebyySwa1aZB6Qz | Loghouse ECO 5.0×3.0 | Price To | *(empty)* | **27090** | same | VERIFIED |
| F5 | rechsZvDCyrdLDrNU | Loghouse ECO 5.0×4.0 | Price To | *(empty)* | **31590** | same | VERIFIED |
| F6 | recwAWG6vylMAuHsD | Loghouse ECO 6.0×3.0 | Price To | *(empty)* | **31240** | same | VERIFIED |
| F7 | recp2utO11YWRg1qe | Loghouse Studio ECO 5.2×4.7 | Price To | *(empty)* | **40775** | loghouse.ie Studio category 2026-10-06 | VERIFIED |

All 14 rows also had Last Price Check set to 2026-10-06. Every Base Price not listed as changed was
confirmed still equal to its expected old value and left untouched.

## SKIPPED — ALREADY CORRECT
- **recDiJX5C1S3DbbUo** Shomera Classic Base Price — expected 28450, still the published floor. Not touched.
- **recaubl44SGrtcDOX** Loghouse ECO 3.0×3.0 — Price From 14280 / Price To 19890 already match the published range.
- **D · CG Garden Rooms recxdr0chc5ljRqfR** — quote-only status is ALREADY recorded in the organisation note
  ("GARDEN ROOMS: fully bespoke/quote-only, no fixed sizes or prices published"), and Northern Ireland plus
  NI657018 are already in the Headquarters field. No numeric price invented. No new write needed.
- **PS-01/02/03 Power Sheds** — recfb1UXi3nW7ekH4 / recyHNAgh4s50Ol1S / reckjDb8tqpNh29c9 already hold
  EUR 6129 / 6959 / 9199, Verified, one record each. **ZERO WRITES, as directed.**

## STOPPED — INSUFFICIENT FIRST-PARTY VERIFICATION
- **C · Ecohouse Building Systems recUnzSlV4tszVzg6 — all 7 proposed records NOT created.**
  The proposal's figures (€13,299 · €17,969 · €19,049 · €20,049 · €22,099 · €24,179 · €32,499) could not be
  reproduced anywhere on ecohouse.ie on 2026-10-06. The live shop publishes PRICE RANGES inc. VAT, e.g.
  Garden Room 6×4m €27,090–€36,420, Garden Room 5×4m €23,190–€31,590, Garden Room 6×3m €22,840–€31,240,
  Studio 5×4m €27,830–€36,080, Garden Room 9.2×4.4m €42,150–€55,785. None of the seven proposed figures appears.
  The proposal's own MEDIUM-confidence warning anticipated exactly this. Creating records from the
  search-index figures would be manufacturing data, which the authorisation forbids. Ecohouse VAT = Yes was
  also NOT written, because without priced rows it changes nothing in the universe and the organisation note
  already carries the VAT-inclusive statement.
- **Collateral finding:** three Ecohouse published floors (€27,090 / €23,190 / €22,840) are IDENTICAL to
  Loghouse's stored floors for the same rooms, and both publish the same €36,420 ceiling at 6×4m. The
  proposal's "Loghouse ~12% dearer, consistent with a reseller margin" is therefore NOT supported by today's
  evidence. The distinct-organisation verdict (4.1b) is unaffected; the margin inference is withdrawn.

## DEFERRED — SCHEMA CANNOT EXPRESS SAFELY
- **vatRate = 13.5 for Garden Rooms.** Product Pricing has NO VAT Rate field. fldWZgFTIUd4T5tpz is
  "Display Order" (number, precision 0 — cannot hold 13.5), and the generator's PRICING_FIELDS lists no VAT
  Rate, which is why vatRate is null on all 477 products. vatStatus = Yes IS stored. The published 13.5% rate
  is recorded in both new records' Notes so the evidence is not lost. Structured vatRate needs a schema field
  plus a generator change.
- **G · Ecohouse ↔ Loghouse relationship.** The Organisations table has no organisation-to-organisation
  relationship field. Recording manufacturer→reseller would mean overloading a prose field, which would
  assert a relationship the schema cannot qualify — and the margin evidence that motivated it has just been
  disproved. Not written. Organisations NOT merged. PRODUCT EQUIVALENCE not implemented.

## GRANULARITY DEVIATION (recorded, not hidden)
The proposal asked for 7–8 Garden Rooms records and 6 Shomera records. Atlas holds **Range** products, not
per-model products: Garden Rooms has 3 products (CUBE Range, Ultimate Range, Bespoke) and Shomera has 5
(Classic Range, Contemporary Range, 3 "For Life" studios). Creating Products was not authorised by Phase 6A.
Four differing Verified records on one Range product would also have driven `adjudicate_price()` to rule 4
(equal authority, disagreement) and made the product **ambiguous**, destroying its price. One range-level
record per existing Range product is the smallest correct action; the full per-model grids are preserved in
the Notes. ULTIMATE 27 (€51,000 ex-VAT, no published inclusive total) is therefore not a governed price.
