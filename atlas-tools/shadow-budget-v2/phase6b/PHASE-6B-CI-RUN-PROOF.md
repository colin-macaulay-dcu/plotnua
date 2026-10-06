# PHASE 6B · CI RUN PROOF AND FINAL DECISION
**6 October 2026 · VERDICT: NO-GO for live five-band integration.**

## A · CI WORKFLOW RUN PROOF
| | |
|---|---|
| Workflow | `.github/workflows/atlas-match-qualification-dry-run.yml` |
| Run | **#6**, id **37460970253** |
| URL | https://github.com/colin-macaulay-dcu/plotnua/actions/runs/37460970253 |
| Source commit | **651012a194a5f22cdc5f98cc9ffe4758fca4b99c** on `main` (local HEAD == origin/main, 0 ahead / 0 behind — **no push was needed**) |
| Trigger | `workflow_dispatch`, manually, by colin-macaulay-dcu |
| Result | **Success**, total 1m 19s (job `qualify` 1m 13s) |
| Generated | `2026-10-06T12:08:09Z` |
| Atlas provenance | `sourceBase: appoLZFWesvoPhZGR`, rule `garden-room-qualification-v1`, read-only via `secrets.AIRTABLE_TOKEN` |
| Artefact | `garden-room-qualification-v1-dry-run`, 471 KB, `sha256:dd137852e910f6abfc6fcd40ef5fe68e23d52dc23a9a397c13f2be2ace7db1f0` |
| Raw snapshot | **NOT produced** — see below |
| Repo not modified | `permissions: contents: read`; the workflow's own "Verify the repository was not modified" step ran and the job succeeded |
| Atlas writes | none — job summary: "NOTHING WAS WRITTEN TO AIRTABLE. NOTHING PRODUCTION WAS TOUCHED." |

**Snapshot not enabled, deliberately.** The workflow declares `on: workflow_dispatch:` with **no inputs**, and invokes the generator with `--out-dir` only — it never passes `--write-snapshot`. Enabling it is a workflow edit, i.e. a commit and push, which this phase forbids. No workflow defect was found, so the workflow was left untouched.

## B · ARTEFACT PROVENANCE — AND WHY IT CANNOT PASS THE PRODUCTION GATE
Read directly from the artefact: `schema: plotnua.garden-room-recommendation-universe`,
`version: **"1.0.0-dryrun"**`, `**dryRun: true**`, `generated 2026-10-06T12:08:09Z`,
`sourceGardenRoomCount: 575`, `eligibleCount: 573`, `excludedCount: 2`.
**No `governedDigest`. No `organisationCount`.**

The dry-run workflow is a *preview* path. The generator stamps its output `dryRun: true`.
The Phase 5 production promotion contract therefore **cannot** be satisfied by this artefact,
and the gate was **not** weakened to make it pass. STOPPED, as instructed.

The correct production path already exists: **`atlas-match-universe-refresh.yml`**, which has
`workflow_dispatch` with a mode input whose **`verify-only`** setting "generate[s], validate[s]
and upload[s] the candidate artefacts, then STOP[s] without touching production". That is the
next dispatch.

## C · SECTION 2 — EVERY REQUIRED FACT VERIFIED IN THE GENUINE ARTEFACT
| required | found | |
|---|---|---|
| PROD-000383 €6,129 EUR adjudicated cc=1 | €6,129 EUR, `adjudicated`, `candidateCount 1`, verified | PASS |
| PROD-000384 €6,959 EUR adjudicated cc=1 | €6,959 EUR, `adjudicated`, `candidateCount 1`, verified | PASS |
| PROD-000382 €9,199 EUR adjudicated cc=1 | €9,199 EUR, `adjudicated`, `candidateCount 1`, verified | PASS |
| Garden Rooms — two Phase 6A Range records | CUBE €36,500 · Ultimate €43,650, both verified / adjudicated / cc=1; Bespoke correctly unpriced | PASS |
| Shomera — revised Range pricing | Classic €28,450 · Contemporary **€36,450**; three For Life studios quote-only | PASS |
| Big Man — no €60,000–€70,000 | `price: null`, `adjudication: "missing"`, state `quote-only` | PASS |
| Loghouse — Price To / range-floor | all 8 carry ceilings: 19,890 / 22,920 / 27,090 / 27,090 / 31,590 / 31,240 / **36,420** / 40,775, VAT `Yes` | PASS |
| Ecohouse — no rejected seven | all **29** Ecohouse products `price: null`, state `missing` | PASS |
| rejected seven anywhere in the artefact | **zero occurrences** | PASS |

Every one of these emerged naturally from live Atlas. No patch, no merge with the Phase 5
projection, no correction overlay.

## D · TWO BLOCKERS THE REAL ARTEFACT EXPOSED

**D1 · The universe is 573 products / 64 organisations, not 477 / 65.**
Every band figure produced in Phases 5 and 6A was computed on the **stale operative artefact**.
Real post-write totals: no usable price **259**, EUR usable **257**, GBP usable **54**, other
currency **3**. Price-evidence state: verified 278, present-unverified 53, quote-only 21,
missing 221. Adjudication: adjudicated 314, **ambiguous 17** (independently confirming the 17
found earlier), missing 22, none 220. The earlier five-band population (43/43/26/13/9) is
**superseded and must not be used**.

**D2 · The production generator does not emit the five-band inputs.**
Measured against every product in the artefact, these are **ABSENT**: `priceSafeForMatching`,
`priceBasisClass`, `priceBasisConfidence`, `priceIsRangeFloor`, `vatStatus`, `vatRate`,
`priceEvidenceRef`, `priceRecordIds`. What it does carry is raw
`priceEvidence{base, from, to, includesVat, status, priceType, quoteOnly, evidenceScope,
adjudication, candidateCount}` — the right ingredients, not the derived contract.

Consequently the 48 proofs and the safety-gated five-band population **cannot** be run against
this artefact without synthesising the missing fields — which is precisely the overlay
simulation this phase forbids. Sections 4, 6 and 7 are therefore **not reported**, rather than
reported on invented inputs.

**Observation to confirm (not asserted as fact):** the artefact's `priceBasis` field holds
`{Verified 272, Partially Verified 29, Draft 8, Researching 8, Active 4, Archived 1, null 251}`
— these are price-record *Status* values, not a basis-of-supply classification. Worth checking
before the generator is widened, since the five-band basis line depends on that name.

## E · SECTION 5 — LEGACY SAVED-BUDGET MIGRATION · 18/18 PROVED
`atlas-tools/shadow-budget-v2/phase6b/legacy-budget-migration.mjs` + its proof.
- stored amount < €50,000 → `30k-50k`; ≥ €50,000 → `50k-plus` (boundary is `>=`, proved)
- **no stored amount → `needs-choice`**, offering exactly `30k-50k` / `50k-plus`. A legacy
  answer is never defaulted, because that would invent a budget the homeowner never gave.
- `null`, `NaN` and the *string* `"45000"` are all treated as *missing*; `0` is a real amount.
- **The axis cannot disappear:** every input — including `{}`, `null`, `undefined`, `''`,
  `'nonsense'` and `'  30k-plus  '` — resolves to a defined status; `budgetKeyForRanking`
  returns `null` only when a question is owed, and never returns the retired key.

## F · CORRECTED LIVE DIFF
**A · `your-plot.html`** — `AS_BUDGET_BANDS` at line 15658 → five keys; `30k-plus` retired;
live lookup at line 17151 (×2); safety-aware `budgetFit` (present only when
`priceSafeForMatching === true`); homeowner basis line from `priceBasisClass`; `From` from
`priceIsRangeFloor`; VAT clause from `vatStatus` only, never inferred; **plus the legacy
`30k-plus` migration above, including the `needs-choice` prompt.**
**B · generator** — widen to emit the governed price contract (the 13 fields in D2) and produce
a **production** artefact with `governedDigest` and `organisationCount`; no change to
`adjudicate_price()` or `price_record_number()`.
**C · operative universe** — wholesale replacement by the CI-generated candidate, never hand-edited.
**DO NOT CHANGE** `garden-room-detail-typicalhomeowner-v1.json` or
`garden-room-detail-evidence-v1.json` — their single `10k-20k` is homeowner prose
("working to roughly EUR 10k-20k") at `/products/rec280lNwFUpajNBI/typicalHomeowner/text`.

## G · KNOWN EXCLUDED DEFECTS
1. Generator does not emit the five-band contract (**blocks the release**).
2. No production-mode artefact yet — dry run only; no `governedDigest`.
3. Ecohouse unpriced; the seven rejected figures remain locked out pending separate authorisation.
4. 17 pre-existing ambiguous products (duplicate equal-authority records).
5. €50k+ overshoot unfixed and open-ended.
6. Structured `vatRate` has no Atlas field; 13.5% stays prose.
7. ULTIMATE 27 (€51,000 ex-VAT) not a governed price.
8. Power Sheds price type is the whitespace variant `"    Standard Price"` — confirmed in the real artefact.
9. `priceBasis` appears to carry Status values (see D2 observation).
10. Raw snapshot not produced, so this Atlas read is not replayable.

## H · DECISION — **NO-GO**
The writes are correct and now proven live. The release is not, because the artefact that would
justify it is a dry run that does not carry the five-band contract.

**Order to GO:** widen the generator (B) → dispatch `atlas-match-universe-refresh.yml` in
`verify-only` → run the production promotion contract → 48 proofs + 15 locks + 18 migration
checks on the real candidate → recompute the five bands on **573** → re-run the eight
simulations → then integrate.
