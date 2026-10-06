# PHASE 6C · THE REAL GOVERNED CANDIDATE — CONSOLIDATED DECISION
**6 October 2026 · VERDICT: NO-GO for live five-band integration.**
**The five-band hypothesis is NOT supported at the top by the 573-product evidence.**

## A · GENERATOR CHANGE (committed `e7c7e9c`, on main)
175 insertions, **0 deletions**, purely additive. Emits all 13 governed fields plus
`organisationCount`, `governedDigest`, `governedPriceContractVersion`, `sourceKind`.

## B · priceBasis — DIAGNOSED, RESOLVED, AND A SELF-CORRECTION
`match_price()` returns `cell(rec,"Status")` as its third value; the emit block assigned it to
`priceBasis`. It has never carried commercial basis — it carries the record's VERIFICATION STATUS.
**Correction to my earlier claim:** I said nothing read it; that was wrong, a truncated grep.
`your-plot.html` reads it **19 times** and already treats it correctly as a status
(`comparePriceEvidenceState()` → the three-state Transparent Pricing surface). So this is a
**naming defect, not a live truth defect**, and removal would be unsafe. `priceStatus` added as the
truthful name; `priceBasis` retained unchanged, marked deprecated, and barred as a basis source.

## C–D · GIT, COMMIT, PUSH
Push was rejected because the scheduled Atlas-statistics workflow landed `63da7c5` mid-phase.
Rebased (no force, no amend of published history) → `e7c7e9c`, fast-forward. Five DISC-026 files
verified **byte-identical** across the rebase; both stashes untouched; staged set exactly 2 paths.

## E · VERIFY-ONLY CI RUN
| | |
|---|---|
| Run | **#37**, id **37477354073**, `atlas-match-universe-refresh.yml` |
| Commit | **e7c7e9c** on `main` · mode **verify-only** |
| Result | **Success**, 1m 42s (job 1m 36s) |
| Artefact | `garden-room-universe-candidate`, 975 KB, `sha256:c43a6bcfad488cfc427a7a3e325dd9c571922edff36a3c66e61f272b306e4a86` |
| Validation | **VALID — candidate is safe to publish** (products 573, uniqueCanonicalIds 573, numericPrices 314) |
| Production | **NOT replaced** — verify-only stopped before publication |

## F · CANDIDATE PROVENANCE
`generated 2026-10-06T14:16:28Z` · `sourceBase appoLZFWesvoPhZGR` · **`sourceKind: airtable-live`** ·
`governedPriceContractVersion garden-room-price-contract-v1` ·
**`governedDigest 497d82aa42909b72e5eb56bbbff9105c5010bd296fdab7815d122e9571fb4523`** ·
`organisationCount 64` · all 13 governed fields present on **573/573** · deprecated `priceBasis`
alias retained on 573/573.

**REMAINING DEFECT:** the artefact still carries `dryRun: true` and `version: "1.0.0-dryrun"`.
These are hardcoded in the generator and were NOT in this phase's authorised scope. The refresh
path is the real production path, so the candidate currently mis-describes itself. Must be fixed
before any publication.

## G · GUARDS
- **51/51** price-contract proofs (incl. guard-capability: reintroducing a marketing token and
  reintroducing VAT inference each make the suite fail)
- **68/68** existing generator provenance proofs
- **18/18** legacy `30k-plus` migration proofs
- **NOT YET RUN on this candidate:** the 48 Phase-5 proofs and the 15 Phase-6B locks. They are node
  scripts in the sandbox; the artefact was read inside the browser. **Overlap note:** the 15 locks
  and the 48 overlap on G11/G12 and on prose containment, so the honest combined figure is **not**
  48+15+18=81. Unique checks across all suites ≈ **126**, of which **137 have been executed** only
  if double-counted — which is why they are reported separately above rather than summed.

## H · 573-PRODUCT UNIVERSE (measured from the genuine candidate)
| | count | organisations |
|---|---|---|
| total products | **573** | **64** |
| no usable price | 259 | 31 |
| EUR usable | 257 | 29 |
| GBP usable | 54 | 14 |
| other currency | 3 | 1 |
| **safe EUR usable** | **250** | **24** |
| **unsafe / conflicted EUR** | **7** | 6 |
| range-floor | 98 | |

Basis classes: `ERECTED_SERVICES_UNKNOWN` 156 · `KIT_SELF_ASSEMBLY` 89 · `UNKNOWN` 328.
**No `ERECTED_WITH_SERVICES`** — delivery and site-works remain UNKNOWN by design.
Erection axis: INCLUDED 156 · EXCLUDED 89 · UNKNOWN 328.
Confidence: NO_PRICE 242 · NO_BASIS_STATED 119 · EXPLICIT 107 · NOT_CONFIRMED 70 · UNSAFE 18 ·
**CONFLICTED 17** (the pre-existing ambiguous set, now correctly reported as conflicted rather than
as missing — the defect my own guard caught).
VAT: Unknown 391 · Yes 157 · No 25 · **vatRate populated: 0**.

## I · SUPPLIER-WEIGHTED DISTRIBUTION
24 suppliers carry any safe EUR price. Their **entry** (lowest safe) prices:
lowest **€3,624** · median **€10,851** · highest **€42,000**. Highest safe price anywhere €149,900.

| band | products | suppliers | suppliers whose ENTRY price sits here |
|---|---|---|---|
| Under €10,000 | 109 | 9 | 9 |
| €10,000–€20,000 | 89 | 14 | 8 |
| €20,000–€30,000 | 32 | 10 | 3 |
| €30,000–€50,000 | 14 | 8 | 4 |
| **€50,000+** | **6** | **1** | **0** |

## J · FIVE-BAND VERDICT — **€30–50k YES, €50,000+ NO**
Cheapest/median/dearest by band: €3,624/€7,267/€9,995 · €10,047/€13,489/€19,995 ·
€20,400/€22,720/€29,700 · €30,610/€38,725/€49,750 · €84,900/€117,400/€149,900.

**€30,000–€50,000 is supported**: 14 products across 8 distinct suppliers, well spread.

**€50,000+ is not a market, it is one maker.** 6 products, **1 supplier (ÖÖD House)**, and **zero**
suppliers whose entry price falls in the band. There is a **dead zone with nothing between €49,750
and €84,900**. A homeowner choosing "€50,000+" is routed to a single supplier — which is a
concentration claim PlotNua cannot stand over as a band.

Per instruction I have **not** invented a €75k boundary. The honest options are to merge the top
into **€30,000+**, or to keep €50,000+ while disclosing that it currently resolves to one maker.
That is a founder decision, not mine.

## K · EIGHT SIMULATIONS (current live vs real candidate)
| wallet | LIVE band | prod/sup | × | CANDIDATE band | prod/sup | × |
|---|---|---|---|---|---|---|
| €8,000 | under-10k | 43/10 | 1.2 | under-10k | **109/9** | 1.2 |
| €15,000 | 10k-20k | 45/13 | 1.3 | 10k-20k | **89/14** | 1.3 |
| €25,000 | 20k-30k | 29/9 | 1.2 | 20k-30k | **32/10** | 1.2 |
| €35,000 | 30k-plus | 24/12 | **4.3** | 30k-50k | **14/8** | **1.4** |
| €45,000 | 30k-plus | 24/12 | **3.3** | 30k-50k | **14/8** | **1.1** |
| €60,000 | 30k-plus | 24/12 | 2.5 | 50k-plus | **6/1** | **2.5** |
| €80,000 | 30k-plus | 24/12 | 1.9 | 50k-plus | **6/1** | 1.9 |
| €120,000 | 30k-plus | 24/12 | 1.2 | 50k-plus | **6/1** | 1.2 |

**€35k named:** Concept Modular 25m² From €49,750 (KIT, ex-VAT) · Iglucraft Igluoffice 2 From
€48,000 · **Garden Rooms Ultimate From €43,650 (VAT Yes)** · Garden Office Solutions 26.4m² €43,600
· Modular House Studio From €43,450 · **Garden Rooms CUBE From €36,500** · **Shomera Contemporary
From €36,450** · Loghouse Studio ECO From €30,610.
**€60k named — all six are ÖÖD House:** Big Monolith €149,900 · Glääzy €139,900 · Möön €139,900 ·
Extended €94,900 · Mobile €89,900 · Signature €84,900.
**The €60k overshoot is unchanged at 2.5× and is now additionally a single-supplier band.**

## L · LEGACY MIGRATION — 18/18
`<€50k → 30k-50k`, `≥€50k → 50k-plus`, no amount → **needs-choice**, never defaulted; the axis
cannot disappear on any input.

## M · PROPOSED LIVE DIFF (unchanged, NOT applied)
A `your-plot.html` five-band map + safety-aware budgetFit + basis line + From + VAT + legacy
migration · B generator: fix `dryRun`/`version` for the production path · C operative universe
replaced wholesale by the CI candidate.
**DO NOT CHANGE** `garden-room-detail-typicalhomeowner-v1.json` or
`garden-room-detail-evidence-v1.json` — their `10k-20k` is homeowner prose.

## N · KNOWN EXCLUDED DEFECTS
1. `dryRun:true` / `1.0.0-dryrun` on the production candidate. 2. €50,000+ = one supplier.
3. €49,750–€84,900 dead zone. 4. Delivery and site-works axes unmeasured → 328 UNKNOWN basis.
5. 17 conflicted products. 6. Ecohouse unpriced; seven rejected figures locked out.
7. `vatRate` unstorable. 8. ULTIMATE 27 not governed. 9. 48 + 15 suites not yet run on this candidate.

## O · **NO-GO**
The generator change is correct and proven; the candidate is genuine, validated and digest-stamped.
The five-band architecture is **not** ready because its top band fails on the new evidence.
