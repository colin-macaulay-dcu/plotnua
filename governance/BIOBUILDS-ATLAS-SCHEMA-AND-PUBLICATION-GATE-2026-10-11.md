# BIOBUILDS · ATLAS SCHEMA AND PUBLICATION GATE — PHASE 1 DESIGN

**Design and report only. 11 October 2026.**
Nothing in Airtable, Atlas, the generated JSON, the private preview or public
visibility has been changed by this document. No supplier email.

---

## 0 · Two corrections to my own earlier work

### 0.1 Approval status

An earlier audit note of mine said public publication "is not authorised".
Wrong, and the distinction is the hinge of this whole design.

BIOBUILDS **granted** permission in writing on 2 October 2026, recorded as
`C2-GRANT-BIOBUILDS-20261002` (`rec6JPwNYPIj7EIfZ`) against `ORG-000153`
(`recjNpnrIr2KT5BWh`), outcome *Granted with Conditions — Founder Confirmed*:

> "Yes. We are happy for PlotNua to feature BioBuilds and use selected images
> from our website, with credit and a link back to us. We supply the Republic
> of Ireland. Please send us the listing before it goes live, so we can check
> it."

That is a grant. The last sentence is a **condition attached to a grant**, not
the withholding of one. The 11 October email is that condition being
exercised: Mateus reviewed, asked for factual corrections, and those
corrections are now applied (`edecc86`, `7b81224`) and awaiting his
confirmation.

| Dimension | State |
|---|---|
| Feature / image permission | **GRANTED** — 2 October 2026 |
| Corrected listing review | **AWAITING CONFIRMATION** — corrections applied 11 October |
| Public visibility | **HOLD UNTIL REVIEW COMPLETE** |

No further permission will be requested. BIOBUILDS said yes once; asking again
would misread their reply. BIOBUILDS is also **not** a preview-only supplier
and must not be added to `atlas-tools/preview-only-suppliers.json`, whose own
rule is "UNKNOWN is not GRANTED". BIOBUILDS is the opposite case.

### 0.2 The Cluster 1 guard — my audit was wrong

My audit stated that populating Wanderlust's area would push
`class3aCandidateCount` from 2 to 3 and trip the refusal at
`atlas-tools/build-cluster1-garden-authority.py:59` (`if N_3A > 2`).

**That is incorrect.** Requirement F was written on the strength of it, so it
matters. Measured:

| Counter | Source population | Value |
|---|---|---|
| `cluster1-cost-evidence.json → class3AProductsInAtlas` | `garden-room-recommendation-universe-v1.json`, **573 records, all `Garden Rooms`** | 1 |
| `additional-home-universe-v1.json → class3aCandidateCount` | 46 records, all `Additional Home` | 2 |

BIOBUILDS products carry `productCategory: "Additional Home"`. Searching the
garden-room universe returns **0 BIOBUILDS records**. The two counters measure
two disjoint populations and are not connected.

**Consequence: the Cluster 1 guard is not affected, needs no re-approval, and
must not be touched.** Requirement F is satisfied by doing nothing to it.

The proportionate response is not a change but a test: assert that the two
populations stay disjoint, so a future refactor cannot quietly couple an
Additional Home count to garden-room copy. That is guard **PG9** below, and it
costs one assertion.

---

## 1 · Proposed schema

Adopting Option A as decided. Four changes, each the smallest that carries the
truth.

### 1.1 Named price configurations

```jsonc
"price": {
  "state": "VERIFIED_NUMERIC_PRICE",
  "basis": "INCLUDES_VAT",          // INCLUDES_VAT | EXCLUDES_VAT | VAT_UNKNOWN
  "vatRatePercent": 23,             // null unless the supplier states it
  "currency": "EUR",
  "configurations": [
    { "key": "exterior-finished", "label": "Exterior Finished",
      "amount": 105000.0, "priceType": "Published Price" },
    { "key": "turnkey",           "label": "Turnkey",
      "amount": 163000.0, "priceType": "Published Price" }
  ],
  "amount": 105000.0,               // RETAINED, = lowest configuration
  "priceType": "Published Price"    // RETAINED
}
```

- `configurations` is **ordered cheapest first**, and the order is part of the
  contract, so a renderer can take `[0]` without re-deriving anything.
- `amount` is retained, not deprecated-and-removed, and always equals the
  lowest configuration. This is what makes the change compatible: every
  existing consumer keeps working and shows the entry price rather than an
  arbitrary one. Removing it is a later decision, not part of Phase 1.
- `basis` is **required wherever an amount exists** and has no safe default.
  `VAT_UNKNOWN` is a real state that must never render as though it were
  VAT-inclusive. The current BIOBUILDS records are the argument: they carried
  "+VAT" in prose where no field could see it, and the prose was wrong.

### 1.2 The silent-discard hazard, closed first

`_price_state()` returns on the **first** pricing row carrying a number. Add a
second row today and the generator takes one arbitrarily and discards the
other, with no flag. Atlas would publish a verified-looking figure that is
simply the wrong one, and every existing guard would pass.

So before any Airtable row is added:

```python
numeric = [r for r in price_rows if _amount_of(r) is not None]
if len(numeric) > 1 and not _has_configurations(price_rows):
    return ("PRICE_AMBIGUOUS_MULTI_ROW", None, None, None)
```

A held state, not an eligible one. It says what is true: more than one price
is published and Atlas cannot yet say which to show. This lands **first**, so
the window in which a careless row could publish a wrong price never opens.

### 1.3 Commercial terms

A price without its boundary is not safe to publish. €105,000 is honest only
beside what it does and does not buy.

```jsonc
"commercialTerms": {
  "included":   [ {"key":"transport","text":"Transport to Ireland"},
                  {"key":"assembly","text":"Assembly on prepared ground screws"} ],
  "excluded":   [ {"key":"kitchen","text":"Kitchen furniture and appliances"} ],
  "perProject": [ {"key":"foundations","text":"Foundations"},
                  {"key":"utilities","text":"Utility connections"},
                  {"key":"siteworks","text":"Site works"} ],
  "source": "https://www.biobuilds.com/ie/turnkey",
  "verifiedOn": "2026-10-11"
}
```

Terms that differ by configuration sit on the configuration, not the product.
**Contested terms are omitted, not averaged**: the supplier's own two pages
disagree on ventilation and smart blinds, so neither is claimed, and the
conflict is recorded in the evidence note rather than resolved by guesswork.

### 1.4 Area, and the honesty of "48"

```jsonc
"area": {
  "number": 35.54, "unit": "m²",
  "measurementBasis": "VERIFIED_INTERNAL",
  "text": "35.54 m² / 383 ft² interior, as published by BIOBUILDS.",
  "modelNameNumber": 48,
  "modelNameNumberIsNotArea": true
}
```

The last two fields exist because the failure they prevent already happened:
"48" is the configurator key `SQF_TYPE=wanderlust-48`, not a published area,
and it reached a homeowner-facing page as "Floor area 48 m²". Recording it
explicitly as *not an area* means the next reader cannot repeat the inference,
and PG8 can assert the two never match.

---

## 2 · The publication gate

### 2.1 Principle

Three dimensions, each recorded where it is decided; visibility **derived**
from all three and never hand-set. No single field, and no data-quality
correction, can publish a supplier.

```
permission.state      GRANTED | CONDITIONAL | DECLINED | NONE
listingReview.state   NOT_REQUIRED | AWAITING_CONFIRMATION | CONFIRMED | CHANGES_REQUESTED

publicVisibility = PUBLISHABLE
    only if permission.state   == GRANTED
    and    listingReview.state in (NOT_REQUIRED, CONFIRMED)
    and    assetApprovalState  == APPROVED      (existing Atlas gate)
otherwise HOLD, with holdReason naming which condition failed.
```

This answers requirement C directly: the gate reads permission and review
state only. **`area.number` is not an input to it.** Correcting a measurement
cannot change visibility, because visibility does not look at measurements.

`NOT_REQUIRED` is set from the grant's own wording when the grant is recorded,
and PG4 refuses a grant whose text asks for pre-live review but whose state
claims `NOT_REQUIRED`.

### 2.2 BIOBUILDS today

```jsonc
{
  "organisation": "ORG-000153",
  "permission":    { "state": "GRANTED",
                     "ref": "C2-GRANT-BIOBUILDS-20261002",
                     "record": "rec6JPwNYPIj7EIfZ",
                     "date": "2026-10-02",
                     "scope": ["feature", "imagery"],
                     "conditions": ["credit", "link-back", "pre-live-review",
                                    "withdrawable-on-request"] },
  "listingReview": { "state": "AWAITING_CONFIRMATION",
                     "requestedBy": "supplier",
                     "correctionsReceived": "2026-10-11",
                     "correctionsApplied": ["edecc86", "7b81224"],
                     "confirmedAt": null },
  "publicVisibility": "HOLD",
  "holdReason": "listing-review-awaiting-confirmation"
}
```

`holdReason` is **not** `no-permission`. Anyone reading this learns the true
position: a supplier who said yes, whose corrections we have applied, awaiting
a sign-off they expect to give.

### 2.3 Where it lives

Extend `image-rights-records.json` — it already carries `permission_outcome`,
`conditions`, `permission_date` and the Atlas refs, and already has a prose
`note` doing this work informally. Adding `listing_review` and
`public_visibility` beside them keeps one record per supplier and creates no
fourth register.

---

## 3 · Exact files and Airtable tables affected

### 3.1 Repository

| File | Change |
|---|---|
| `.github/scripts/additional_home_qualification.py` | `_price_state()` → configurations, `basis`, `vatRatePercent`; the multi-row refusal; `_area_evidence()` → `modelNameNumber` passthrough |
| `.github/scripts/generate_additional_home_universe.py` | emit `commercialTerms`; carry the new `price`/`area` shape |
| `image-rights-records.json` · `image-rights-manifest.json` | add `listing_review`, `public_visibility`, `hold_reason` |
| `your-plot.html` | read `configurations[0]` with label; render commercial terms; honour `publicVisibility` |
| `atlas-tools/prove-publication-gate.mjs` | **new** — PG1–PG9 |
| `atlas-tools/prove-publication-gate-capability.mjs` | **new** — one mutation per guard |
| `atlas-tools/prove-biobuilds-containment.mjs` | extend to the public pool, not imagery alone |
| `governance/FOLLOW-UPS.md` | close BB-AIR-001, superseded by this document |

**Not touched:** `build-cluster1-garden-authority.py`, its evidence artefact,
its guards (§0.2), `preview-only-suppliers.json`, the private preview, and
`additional-home-universe-v1.json`, which is generated and never hand-edited.

### 3.2 Airtable

| Table | Field | Type | Note |
|---|---|---|---|
| Pricing | `Configuration` | single select — `Exterior Finished`, `Turnkey` | new; absent = today's behaviour |
| Pricing | `Price Basis` | single select — `Includes VAT`, `Excludes VAT`, `Not stated` | new |
| Pricing | `VAT Rate %` | number, nullable | new |
| Products | `Commercial Terms — Included` / `— Excluded` / `— Per Project` | long text or linked records | new |
| Products | `Model Name Number` | number, nullable | new; for PROD-000523 = 48 |
| Organisations | `Listing Review State` | single select | new |
| Organisations | `Listing Review Confirmed At` | date, nullable | new |

Values for PROD-000523 / PROD-000524 are written only at step 6 of §6.

---

## 4 · Migration for existing products

Additive and null-safe by construction. A pricing row with no `Configuration`
behaves exactly as today, so the other 44 Additional Home products and all 573
Garden Rooms are untouched.

The migration test is a **byte-identity diff**: regenerate the universe after
the generator change and before any Airtable value change, and assert the
output is byte-identical except for the two BIOBUILDS records. If anything
else moves, the generator change was not additive and is rejected.

One real question the diff will answer: products whose `price.basis` is
genuinely unknown become `VAT_UNKNOWN` rather than silently inheriting an
assumption. That is a truthfulness improvement, but it is visible, so it needs
checking against the budget bands (GR-1 to GR-5) before shipping.

---

## 5 · Impact on the public homeowner journey

**During the hold: none.** BIOBUILDS is invisible today and stays invisible.

Three effects when something does change:

1. **Two prices need two labels.** "€105,000" alone is the same half-truth the
   preview correction just removed. Results and Compare must show
   "€105,000 Exterior Finished", and Compare must not place one supplier's
   exterior-finished price beside another's turnkey price as though they were
   alike. This is the largest piece of work in the plan and the one most
   likely to need design input.
2. **Budget bands** read price amounts. `amount` still equals the lowest
   configuration, so banding is unchanged today — but it should be re-checked
   deliberately rather than assumed.
3. **Commercial terms need somewhere to sit** on the product surface. Without
   that, the exclusions exist in data and not in front of the homeowner, which
   is worse than not having them.

---

## 6 · Order of work

1. **PG1–PG9 + the `PRICE_AMBIGUOUS_MULTI_ROW` refusal**, with capability
   proofs. The gate exists before anything can pass through it.
2. **Record the three BIOBUILDS states** in `image-rights-records.json`. No
   Airtable write — this is PlotNua's record of a position already true.
3. **Airtable fields** created empty.
4. **Generator** changes, then the byte-identity diff of §4.
5. **`your-plot.html` consumers**: configuration labels, commercial terms,
   `publicVisibility`.
6. **Airtable values for BIOBUILDS**: prices, VAT basis, terms, descriptions,
   refreshed sources, and `Model Name Number`. **Area last, deliberately**,
   with PG6 proving it changes no visibility.
7. **On Mateus's confirmation**: `listingReview → CONFIRMED`, promote the eight
   exercised assets from *Reference Only — Not Published* to *Approved*, re-run
   containment. Only then does `publicVisibility` derive to `PUBLISHABLE`.

Steps 1–6 are all safe while the review is outstanding. Step 7 is one state
change plus an asset promotion, because everything else is already satisfied.

---

## 7 · Tests required before implementation

### Publication gate — `prove-publication-gate.mjs`

| ID | Assertion |
|---|---|
| PG1 | `publicVisibility` is derived, never literal; a hand-set value is an error |
| PG2 | A supplier at `HOLD` appears in no runtime payload, no sitemap, no public page |
| PG3 | `GRANTED` + `AWAITING_CONFIRMATION` ⇒ `HOLD` — **requirement G** |
| PG4 | A grant whose evidence matches /before it goes live⎮check it⎮send us the listing/i cannot carry `NOT_REQUIRED` |
| PG5 | `holdReason` never says `no-permission` where `permission.state == GRANTED` |
| PG6 | Changing `area.number` on a held supplier does not change `publicVisibility` — **requirement C** |
| PG7 | `price.basis` present wherever an amount exists; `VAT_UNKNOWN` never renders as VAT-inclusive |
| PG8 | `modelNameNumber` ≠ `area.number` where `modelNameNumberIsNotArea` |
| PG9 | The garden-room and additional-home Class 3A populations stay disjoint — **requirement F**, §0.2 |

### Capability proof — `prove-publication-gate-capability.mjs`

One deliberate mutation per guard, disposable tree per case, control run
first. BLIND, VACUOUS and MISATTRIBUTED all counted as failures. PG3 and PG6
get the sharpest mutations, since they are the two the founder named.

### Regression

Byte-identity diff (§4) · existing BIOBUILDS containment + capability ·
preview-only containment · landmarks · search acceptance ·
`build-cluster1-garden-authority.py` unchanged and still passing ·
`node --check` on `your-plot.html`.

### The end-to-end test requirement G asks for

Drive the real Results journey with the corrected BIOBUILDS data loaded and
`listingReview: AWAITING_CONFIRMATION`, and assert BIOBUILDS appears nowhere
in the rendered output — not in Results, not in Compare, not in the
alternatives carousel, not in any payload. Then flip only `listingReview` to
`CONFIRMED` in a disposable copy and assert it *does* appear, which proves the
test is not passing vacuously.

---

## 8 · Decisions needing founder approval

1. **Serenity's 95 m² area.** Measurement basis is unverified. Options:
   leave `area.number` null as today (honest, keeps it out of the pathway); or
   verify the basis with BIOBUILDS and populate. **I recommend leaving it
   null.** It sits outside the 32–45 m² band either way, so populating buys
   nothing and risks publishing an unverified measurement. It is also not
   something to add to Mateus's current review — it can wait.
2. **How Compare handles configurations.** Comparing one supplier's turnkey
   price against another's shell price is misleading even when both are
   labelled. Options: compare like-for-like only; show both and refuse to rank
   on price; or defer Compare until more suppliers carry configurations. This
   is a product judgement, not an engineering one.
3. **Whether `amount` is retired later.** Phase 1 keeps it. Removing it is
   cleaner but touches every consumer; worth doing deliberately, not now.
4. **The unverified specification claims.** Passivhaus certification,
   ≤0.4 ACH@50, ~15 kWh/m²/yr, carbon-negative EPD and "~3-week move-in" are
   carried as fact in both descriptions, sourced to an August catalogue read.
   Re-verify, or demote to attributed claims, before public publication.

---

## 9 · What this design refuses to do

- Ask BIOBUILDS for permission again. They granted it on 2 October.
- Classify BIOBUILDS as preview-only, unapproved, or unknown.
- Let a data-quality correction publish a supplier.
- Let one price stand for two, or a price stand without its VAT basis and its
  exclusions.
- Weaken, bypass or re-stamp the Cluster 1 guard, which §0.2 shows is not
  involved.
- Resolve a supplier's contradictory pages by choosing the flattering reading.
