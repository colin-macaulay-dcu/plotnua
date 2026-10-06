# PROPOSED ATLAS UPDATE SET — Garden Room price evidence
**Status: PROPOSED ONLY. Nothing in this file has been written to Airtable or Atlas.**
Recorded 6 October 2026. Authorisation required per update class.

Phase 4 §6: research findings are not silently baked into code. The shadow
universe deliberately EXCLUDES everything below, and `shadow-recommendation-universe-v2.json`
records that exclusion in `newEvidenceDeliberatelyExcluded`.

---

## CLASS 1 · VERIFIED FIRST-PARTY UPDATE

### 1.1 Garden Rooms (gardenrooms.ie) — NEW PRICING, 7–8 records
Organisation exists in Atlas (`rechco59Sn6wp3Aiq`, 3 products, 0 priced).
Source: gardenrooms.ie/designs/cube-range/ and /ultimate-range/, read 6 Oct 2026.

| model | size | Base Price (ex-VAT) | published total | VAT |
|---|---|---|---|---|
| CUBE 17 | 3.6×4.8m | 32,159 | **36,500** | Yes, 13.5% published |
| CUBE 20 | 3.6×5.5m | 34,247 | **38,870** | Yes, 13.5% |
| CUBE 23 | 3.6×6.4m | 39,163 | **44,450** | Yes, 13.5% |
| CUBE 25 | 3.6×7m | 42,159 | **47,850** | Yes, 13.5% |
| ULTIMATE 20 | 4.6×5.6m | 38,458 | **43,650** | Yes, 13.5% |
| ULTIMATE 23 | 4.6×6.4m | 43,833 | **49,750** | Yes, 13.5% |
| ULTIMATE 25 | 4.6×7m | 47,269 | **53,650** | Yes, 13.5% |
| ULTIMATE 27 | 4.6×7.5m | from 51,000 | *not published* | — |

- Price Type: **Starting From** ("Prices From", "FROM:").
- Scope: **Product-Specific**.
- Basis axes: erection INCLUDED, siteWorks INCLUDED, delivery EXCLUDED → **ERECTED_WITH_SERVICES**.
- Basis notes to record: post foundations in concrete; full electrical package
  (sockets, fuseboard, smoke alarm, LED spots, 2kW heater); plastered and skimmed;
  Firestone EPDM; vertical cedar cladding.
- Known Exclusions to record: delivery Greater Dublin €360 ex-VAT; electric
  connection to the house €24/linear m; toilet €2,800; shower room €4,300;
  partition €2,100; varnish €620–950; skip €360; CAT6 €385.
- **DECISION REQUIRED:** store the ex-VAT subtotal or the published VAT-inclusive
  total as Base Price? Recommendation: **the inclusive total**, with VAT = Yes and
  rate 13.5%, because that is the figure the homeowner is quoted and it is the
  only supplier in the universe publishing both. ULTIMATE 27 has no published
  inclusive figure, so record it ex-VAT with VAT = No rather than grossing it up.

### 1.2 Shomera — PRICE REVISION, 5 records changed + 4 new
Organisation `recw124UIanKV5Ath`, currently 2 of 5 products priced.
Source: shomera.ie/garden-rooms/, fetched and read first-party 6 Oct 2026.

| model | size | Atlas now | proposed | Δ |
|---|---|---|---|---|
| Shomera 12 | 3.0×3.6m | 28,450 | 28,450 | — |
| Shomera 14 | 3.0×4.2m | 35,950 | **36,450** | +500 |
| Shomera 21 | 3.6×5.4m | 38,950 | **39,450** | +500 |
| Shomera 18 | 3.6×4.8m | 41,450 | **41,950** | +500 |
| Shomera 25 | 3.6×6.6m | 44,450 | **44,950** | +500 |
| Shomera 23 | 3.6×6.0m | 46,450 | **46,950** | +500 |

Atlas holds the Classic and Contemporary records as RANGE rows ("Range spans 3
models…"). Proposal: six Product-Specific rows, one per model.
Basis axes: erection INCLUDED, siteWorks INCLUDED, delivery UNKNOWN →
**ERECTED_WITH_SERVICES**. Quote to record: "site survey, design, planning,
build, and installation"; "electrical fittings as standard, with optional
plumbing". VAT: **Unknown — not stated, do not infer.** Price Type: Starting From.

### 1.3 Ecohouse Building Systems — NEW PRICING, 7 of 29 products
Organisation `recUnzSlV4tszVzg6`, 29 products, 0 priced.
€13,299 · €17,969 · €19,049 · €20,049 · €22,099 · €24,179 · €32,499.
SIP construction; **fitting included**; free delivery Leinster, €1.70/km beyond.
Basis axes: erection INCLUDED, siteWorks UNKNOWN, delivery CONDITIONAL →
**ERECTED_SERVICES_UNKNOWN**. VAT Unknown.
**Confidence MEDIUM** — figures read from the site's own shop listing via search
index; recommend one direct product-page read per model before Status = Verified.
**Do not price all 29.** Phase 3 §4: enough to establish entry, middle and top.

---

## CLASS 2 · QUOTE-ONLY STATUS

### 2.1 CG Garden Rooms (CG Joinery) — QUOTE_ONLY_CONFIRMED
Organisation `recxdr0chc5ljRqfR`, 6 products, 0 priced.
Evidence: "cost depends on size, specification and site access rather than a
fixed price list… written fixed quotation covering the build, delivery and
installation, so there are no additions later."
- Record as quote-only. **Do not create a numeric price.**
- Basis IS knowable without a number: erection INCLUDED, siteWorks INCLUDED,
  delivery INCLUDED → **ERECTED_WITH_SERVICES**.
- **SEPARATE FINDING:** based at Mayobridge, Newry — **Northern Ireland**. Any
  future price is likely GBP and would never reach a euro band. Worth checking
  whether the Atlas organisation record states ROI availability.

### 2.2 Big Man Tiny Homes — quote-led, see also Class 3
First-party site publishes no price: "prices range depending on finishes",
referring visitors to a separate Big Man Modular site. Record as quote-only.

### 2.3 Koto — INSUFFICIENT_EVIDENCE, context only
Secondary sources report Niwa cabins "from £50,000 delivered and installed in
the UK". **Not confirmed on koto.co.uk by me.** Record as context in the
correspondence/notes layer only; not a governed price. GBP in any case.

---

## CLASS 3 · WITHDRAW UNSAFE PRICE

### 3.1 Big Man Tiny Homes — withdraw the €60,000
Product `rech2D1aCz41kZtc5`, Pricing record `recVzYsqCkxq61nmE`
(Price From 60,000 / Price To 70,000, Custom Quote, Partially Verified).
Its own note already says: *"Indicative only — third-party press figure… Not a
confirmed provider-published price for this specific design."*
First-party checking confirms no published price exists.
- **Proposed action: withdraw from governed pricing** (Status → Archived, or
  clear the numeric and keep the record as provenance). Do not delete the audit
  trail.
- **Consequence to accept knowingly:** this is one of only two suppliers whose
  top price sat in €50–75k. Withdrawing it is the right call on evidence and it
  thins the upper band.

### 3.2 Six further records already flagged unsafe or conflicted
The shadow build suppresses these from strong budget matching today; each needs
an Atlas resolution, not a code workaround:
NOOK €39,000 (attribution unconfirmed) · Rayco €29,500 (Organisation-Wide scope,
covers homes and extensions) · Bertilo €1,249 (third-party German retail, product
not sold in Ireland) · The Ember €11,750 (GBP/EUR conflict) · The Nova Pavillion
17.8m €8,799 and 21.5m €9,799 (Special Price recorded as Standard Price, pages
out of stock, WebSearch-sourced not rendered) · Garden Office Solutions ×4 and
ModPod Nova (two records per product, different figures, different bases).

---

## CLASS 4 · IDENTITY INVESTIGATION

### 4.1 Ecohouse ↔ Loghouse — **RESOLVED 6 Oct 2026. NOT a duplicate organisation.**

Investigated before either side is written, merged or reclassified, as directed.

**VERDICT: two distinct organisations in a manufacturer → reseller relationship
on one shared product line. Do NOT merge. Do NOT deduplicate.**

Evidence for distinct identity:
- **Different premises, same business park.** Ecohouse: Unit 9A, Block 513,
  Grants Rise, Dublin 24, **D24 AK4V**. Loghouse distribution centre: Unit 518a
  Grants Crescent, Greenogue Business Park, Rathcoole, Co. Dublin, **D24 FD63**.
  Adjacent, not identical.
- Different domains, different phone numbers, different trading histories.
- Loghouse publishes **five showrooms** (Kinsealy D17, Glen of the Downs A98,
  Rathcoole D24, Cork T12, Athlone N37). Ecohouse publishes none.
- Loghouse sells a far wider catalogue: garden log cabins, residential log
  cabins, budget residential, hybrid, modular, contemporary, saunas, cladding,
  radiators. Ecohouse is a SIP manufacturer whose sister brands are xtend.ie,
  sipkits.ie, smartfoundations.ie and walis.ie.
- Ecohouse's own Atlas organisation note states it **manufactures** prefabricated
  SIP panels and invites trade visitors to "visit our factory".

Evidence that ONE PRODUCT LINE is shared — this is the real finding:
- **Identical published build-up.** Both publish EPS 150 mm roof at **217 mm**
  total thickness and EPS 100 mm walls at **184 mm** total thickness, with ground
  screws plus insulated SIP, grey UPVC double glazing, grey insulated classic
  metal roof and 11 mm T&G internal cladding. Atlas recorded Ecohouse as "the
  FIRST supplier in Atlas to publish product-level U-values" — Loghouse publishes
  the same build-up figures.
- **Identical delivery rule.** Both: free delivery to Leinster, then
  **€1.70 per kilometre** — and Loghouse names the origin as "our warehouse in
  Rathcoole", the same business park as Ecohouse's unit.
- **Identical stated dimensions under different product names.** Loghouse's
  "ECO GARDEN ROOM 6.0m x 4.0m" spec table states Size **6.2m x 4.4m**;
  Ecohouse's product is named "Garden Room **6.2 x 4.4m**". Same object.
- **Different prices, consistent with a reseller margin.** 6.2×4.4m:
  Ecohouse **€24,179**, Loghouse **€27,090** — Loghouse ~12% dearer.

**Proposed actions (none applied):**
1. Keep both organisations. Record a governed **relationship**, not a merge:
   Ecohouse = manufacturer, Loghouse = reseller of the ECO Garden Room line.
   The evidence proves a shared specification and origin, not shared ownership;
   whether Loghouse buys from Ecohouse or both buy from a third manufacturer is
   **NOT established and must not be asserted.**
2. Flag the **product-level** duplication: the same physical room is in the
   universe twice at two prices. That is legitimate (two routes to buy, two real
   prices) but Results must not present them as two independent options.
3. **Band-architecture impact: NIL.** Loghouse median €21,235 and Ecohouse
   median €20,049 both sit in €20,000–€30,000, so neither €30–50k nor €50k+
   changes whichever way this is recorded. The five-band architecture is safe
   either way. Checked before reporting, not assumed.

**Correction to the Phase 3 Class 1.3 entry above:** Ecohouse VAT is **NOT
Unknown**. Its Atlas organisation record states "euro pricing **inclusive of
VAT**", and Loghouse publishes the same line as "inc. VAT". Record VAT = Yes,
rate not published.

**Correction to the Loghouse records:** Loghouse publishes a RANGE, not a single
price — "€27,090.00 – €36,420.00 Price range … inc. VAT", driven by finish
(Internal T&G + External Thermowood, or Internal Plasterboard + External
Rendering). The stored €27,090 is the floor. **The €36,420 top crosses into
€30,000–€50,000**, which the current records cannot express. This is 4.2 below.

### 4.1b FOUNDER-ACCEPTED IDENTITY RECORD — 6 Oct 2026

Accepted by the founder. Recorded verbatim for the eventual Atlas update
proposal. Still PROPOSED — no Atlas write has been made.

- Ecohouse Building Systems = **distinct manufacturer organisation** (ORG-000180)
- Loghouse = **distinct reseller organisation**
- **shared ECO Garden Room product line evidenced** (identical 217 mm roof /
  184 mm wall build-up, identical €1.70/km-beyond-Leinster rule, identical
  stated 6.2 × 4.4 m dimensions, two different prices)
- **ownership relationship NOT established**
- **do not assert that Loghouse buys directly from Ecohouse**
- **product-equivalence issue to be handled separately from organisation identity**

Directive standing: do NOT merge, do NOT deduplicate the organisations.

### 4.1c FOUNDER-ACCEPTED CORRECTIONS — 6 Oct 2026

**1. Ecohouse Building Systems**
- `vatStatus` = **Yes**
- `vatRate` = **unknown** (no rate published anywhere first-party)

**2. Loghouse**
- published prices are **ranges**, not single figures
- the stored lower figure is a **range floor**
- Airtable **Price To** should eventually be populated
- `priceIsRangeFloor` must therefore become **true**
- the published range **may cross from €20–30k into €30–50k**
  (worked example: ECO 6.0 × 4.0 m publishes €27,090 – €36,420 inc. VAT,
  floor in €20–30k, ceiling in €30–50k)

### 4.1c-note MEASURED EFFECT OF THE ACCEPTED CORRECTIONS

Measured against the shadow universe, not asserted.

- **Ecohouse contributes ZERO priced rows to the universe today.** All 29
  Ecohouse products are unpriced in the operative artefact. The Ecohouse prices
  quoted during the identity investigation (€24,179 at 6.2 × 4.4 m) were read
  first-party from ecohouse.ie and held in Class 1 as a PROPOSED update; they
  are not in the universe. Consequence: `vatStatus = Yes` for Ecohouse is
  correct to record at Atlas level but changes **nothing** in the universe until
  the Class 1 prices are applied. **Correction to an earlier statement of mine:
  the "Ecohouse median €20,049" figure was an Atlas-side reading, not a universe
  measurement, and must not be cited as a universe figure.**
- **Loghouse already carries `vatStatus = Yes`** on all 8 rows, so that half of
  correction 2 is already satisfied.
- **Range-floor flag: 1 of Loghouse's 8 rows is already true.** The correction
  flips the remaining **7**, taking the universe-wide flag from
  **63 of 141 (45%) to 70 of 141 (50%)**.
- **Band architecture is untouched by either correction**, because Ecohouse has
  no priced rows to place and Loghouse's floors stay where they are — a floor
  flag changes presentation ("From €27,090"), not the band the floor sits in.

### 4.1d FUTURE ENGINE ISSUE — PRODUCT EQUIVALENCE

**NOT to be solved in this phase. Recorded only, for a later phase.**

Two separate suppliers may legitimately offer the same physical product at
different prices.

The Results engine must eventually avoid presenting those as two independent
product choices, while **preserving both legitimate supplier routes**.

First evidenced instance: the ECO Garden Room line, offered by Ecohouse
Building Systems (manufacturer, €24,179 at 6.2 × 4.4 m) and by Loghouse
(reseller, €27,090 floor at the same stated dimensions).

Scope notes for whoever picks this up:
- This is a **product-level** concern. It is explicitly NOT an organisation
  identity concern — 4.1b settles identity and must not be reopened by it.
- Both prices are real and both routes are real. Suppressing either would
  remove a genuine purchase route from the homeowner.
- The failure mode to prevent is a Results page that appears to offer two
  independent options when it is offering one room by two routes.
- **No band-architecture consequence.** Loghouse's 8 priced rows all sit in
  €10–30k by stored floor, and Ecohouse has **no priced rows in the universe at
  all**, so no equivalence treatment can move anything into or out of €30–50k
  or €50k+. Measured against the universe, not assumed.
- Nothing about equivalence is implemented, proposed as code, or guarded in
  this phase.

### 4.2 Range-floor flag not derivable for 6 products
Loghouse and Shomera records publish a range in prose while storing a single
Base Price, so no structured field marks them as a floor. The shadow build
derives 63 of the 69 known cases.
**Proposed fix in Airtable, not in code:** populate **Price To** on those
records. Then `priceIsRangeFloor` becomes fully derivable.

---

## NOT PROPOSED
- No change to the live `AS_BUDGET_BANDS`.
- No generator change (including the `dryRun` and VERSION constants, and the
  inherited curator-prose leak in `features.*.text` — both diagnosed, both
  proposed separately, neither touched).
- No replacement of the operative universe.
