# ADDITIONAL HOME RESULTS — TRUE NO-LEAD EQUALITY

> **SUPERSEDED, 12 October 2026 — RETIRED BEFORE IMPLEMENTATION.**
> The architecture below (`#ahCandidateSet` / `#ahCandidateGrid`, a separate
> residential candidate section) was **never built**. The founder directed
> instead that the Additional Home Results page reuse the existing Garden Room
> Results composition, so no-lead equality is now expressed through the shipped
> `#altResults` gallery. **The equality principle in section 1 still governs; the
> markup, selectors and renderers described here do not exist.**
> For the implemented design, read
> `governance/ADDITIONAL-HOME-RESULTS-CHECKPOINT-2026-10-12.md`.
> This document is retained as the decision record only.

**Status: APPROVED ARCHITECTURE. NOT IMPLEMENTED. SUPERSEDED.**
Founder decision, 11 October 2026. Deferred behind the BIOBUILDS release.

**The shipped Results renderer is not modified by this record.** `your-plot.html`
is untouched: the only change it carries is the earlier Option 1 correction,
already released in `0525c21`. This document exists so that the architecture,
the dependency trace and the stated limits survive the gap between approval and
implementation, rather than being re-derived later from memory.

---

## 1 · WHAT WAS DECIDED, AND WHAT IT REPLACES

The founder reviewed two earlier proposals and rejected the smaller one.

| | proposal | outcome |
|---|---|---|
| Option 1 | make the renderer honour `pnCandidateSplit.lead`, so no candidate *claims* preference | **IMPLEMENTED**, released in `0525c21` |
| CSS-only correction | shrink the hero's type and media at no-lead so it reads as a peer | **REJECTED** — position still implied a preference no text asserted |
| True no-lead equality | all four candidates in one equally weighted grid, no hero at all | **APPROVED**, this record |

Option 1 removed the *claim*. It did not remove the *geometry*: the first
candidate by Product Code kept the hero slot, at roughly 4.1x the name size and
2.7x the price size of the other three, under a heading calling them "other
options". That was recorded as an honest limit of Option 1 at the time, and this
decision closes it.

### The founder's decisions, verbatim in substance

1. **Selection** — an inline detail panel below the candidate grid. One panel
   only; selecting another candidate replaces its contents.
2. **Selection is never a recommendation.** An Atlas recommendation and a
   homeowner-selected option are different things and must stay
   distinguishable through Compare, My Plot and all later navigation.
   `originalRecommendation` **remains null** when Atlas has not identified a
   genuine lead.
3. **Sun & Light / Scene 4** — product-specific content is suppressed until a
   candidate is selected, then populated from that candidate's own evidence.
   General property assessment and guidance stay visible throughout.
4. **Heading** — `"{n} possibilities worth exploring"`, rendering exactly
   `4 possibilities worth exploring` at four candidates. The supporting
   explanation must stay accurate at any count.
5. **Containment** — residential no-lead state only. Genuine-lead Results
   unchanged. Garden Room Results unchanged. Every qualification, publication,
   image-rights, pricing and attribution safeguard intact.
6. **No mandatory-image eligibility gate** (decided in the preceding imagery
   audit). Authorised supplier imagery where available; the branded placeholder
   where not; no AI illustration on a named supplier card, preserving
   `validate-image-provenance.js` P7.
7. **Sequencing** — BIOBUILDS ships first, as its own release. This change
   begins only after BIOBUILDS is verified live.

### The approved homeowner copy

> **4 possibilities worth exploring**
>
> Atlas has identified four buildings that meet the current assessment
> criteria. None has been established as a better match for your property.

At counts other than four the sentence must be rebuilt from the same facts
rather than reworded ad hoc. "four buildings" agrees with `{n}`; the second
sentence is count-independent and stands as written.

---

## 2 · THE DEPENDENCY TRACE

`primaryResult` appears **82 times** in `your-plot.html`. Classified against the
residential path as it stands at `0525c21`. This is the part most expensive to
re-derive, which is why it is recorded here in full.

### Already gated off for residential — no work required

Verified at lines 29586-29592, 29707 and 29731 (GATE 1-4, the existing
containment pattern):

- `renderProfileMatch` — GATE 2, hidden; there is no residential decision profile
- `renderCorroborationBand` — GATE 3, forced to 0
- `renderPlotTwist` — GATE 4, forced false
- `selectReasonedAlternatives`, `altPricedPreference`, `altReasonForDisplay`,
  `altTradeOffForDisplay` — Garden Room branches only (28941-28951)
- `describeWhyNotFirst`, `buildAlternativeRationale` — Garden Room only
- `buildResultsGalleryCard` — defined, **zero call sites**
- `resultsBrief` — GATE 1, hidden

### Live on residential, each reading the arbitrary first candidate

These are the real work. Every one takes a new `leadResult` (null at no-lead)
rather than `primaryResult`.

| line | consumer | what it renders today | treatment |
|---|---|---|---|
| 29595 | `buildResultsHero(primaryResult)` | the oversized hero | becomes the per-candidate detail panel |
| 29611 | `buildResultsWhyStartHere` -> `ctx.why` | "why start here" points | per candidate, in its own panel |
| 29620-29635 | `buildSunlightReasoningChain`, `activateResultsSunlightCentrepiece`, `buildPrimaryWorthChecking` | Sun & Light centrepiece and Scene 4, **attributed to PROD-000425 by accident today** | suppressed until selection, then from the selected candidate (decision 2) |
| 29720 | `originalRecommendation = { product: primaryResult.product }` | the session's "original recommendation", captured once, read by Compare and My Plot | **must stay null at no-lead** — the highest-risk line in the change |
| 29724 | `shownIds[primaryResult.product.id]` | Plot Twist exclusion | harmless (twist off); set from all four |
| 29726 | `renderBeforeYouCommit(primaryResult)` | Ask PlotNua context (`askOwnSetContext`) and About the supplier (`renderTrustProfile`) | per candidate, in its panel |
| 29737, 29781 | `renderLensRail(primaryResult, ...)` | lenses compare against the primary | lenses survive; see 4.4 |
| 29752, 29784 | `renderAltResults(primaryResult, alternativeResults)` | the 3 cards plus Local Option dedupe | replaced by the four-card grid |
| 29774 | `data-rail-run` includes the primary's id | repaint race key | rekeyed on the candidate-set signature |
| 27903-27906 | `resultsComparePrimary` -> `raCompareControl` | "Compare with the recommendation ->" | **no referent at no-lead**; already returns null (27864-27865), so cards would otherwise have no action at all |

### The finding that shapes the whole design

**There is no single-product detail surface in PlotNua.** The hero *is* the
detail surface. The only per-product reveal that exists is `openCompareScreen` /
`renderCompare` (30525, 30714), and it is a **two-product comparison against the
recommendation** — structurally impossible when there is no recommendation.

So requirement "selecting a product reveals its own details" cannot be met by
wiring an existing Product Detail page, because none exists. It is met by
**reusing `buildResultsHero` as the detail panel**, invoked per selected
candidate. That is both the smallest honest route and the one that preserves the
genuine-lead experience exactly: same builder, same CSS, same call site.

---

## 3 · THE APPROVED ARCHITECTURE

### 3.1 · DOM

One new section, after `#hmrPropertyFit` (markup ~10475) and before the existing
`#matchPrimary` (10365, which moves below it):

```
#ahCandidateSet                 hidden by default; shown only at residential no-lead
├─ h2#ahCandidateSetHeading     "{n} possibilities worth exploring"
├─ p#ahCandidateSetNote         the approved two-sentence explanation
└─ div#ahCandidateGrid          role="list" — n cards, catalogue order

#matchPrimary                   EXISTING markup, unchanged
                                at no-lead: hidden until a candidate is selected,
                                then holds that candidate's hero as its detail panel
```

### 3.2 · Components

**No new card component.** The cards are built by **`raProductCard`** (27995),
already shipped and proven: it renders authorised imagery with its required
credit, the branded placeholder via `attachImageFallback`, organisation, name,
price and the governed `leadReason`. One thin wrapper, `ahCandidateCard(row)`,
adds the select affordance and nothing else.

**The detail panel is `buildResultsHero(row)`** — the unchanged builder, called
with the selected candidate. Decision 5's "genuine-lead Results unchanged" is
then satisfied structurally rather than by a flag: with a genuine lead,
`#ahCandidateSet` stays hidden and `buildResultsHero(primaryResult)` runs on the
same line it does today.

### 3.3 · CSS

One block scoped to `#screen-match-results.pn-no-lead #ahCandidateGrid`, reusing
the shipped `#altResults` plate tokens — `--pn-plate`, `--pn-hair`,
`--pn-plate-radius`, `--pn-plate-lift` (8635-8641) — so the cards are visually
identical to a surface already approved. No new colour, radius or shadow.

---

## 4 · HOW PRODUCT SECTIONS WORK WITHOUT AN ARBITRARY PRIMARY

### 4.1 · The lead becomes honest, not reassigned

```js
const pnNoLead = pnResidential &&
  !(results[0] && results[0].ctx && results[0].ctx.isPreferred);
const leadResult = pnNoLead ? null : primaryResult;   // never the first candidate
```

Every consumer in the table above takes `leadResult`. `primaryResult` survives
as the destructured first row for ordering and ids only. **Nothing is assigned a
replacement lead** — the null is made explicit and threaded, rather than each
caller special-cased.

### 4.2 · `originalRecommendation` stays null

Line 29720 is guarded by `leadResult`. Atlas never recorded a recommendation, so
the session must not claim one. Compare and My Plot both read this value, which
is why decision 2 names it specifically. A homeowner selecting a candidate sets
a **selection**, a separate and clearly named piece of state; it never writes
`originalRecommendation`.

### 4.3 · Single-product sections at no-lead

Four sections are lead-specific: the Sun & Light centrepiece, Scene 4
reassurance, About the supplier, Ask PlotNua. At no-lead they are hidden until a
candidate is selected, then populated from that candidate — same functions, same
arguments, one source per section. `hmrLeadEvidence` already behaves exactly this
way after Option 1, so this extends a shipped pattern rather than inventing one.

### 4.4 · Lenses survive

`renderLensRail` takes `leadResult`, which may be null. `raCompareControl`
already returns null without a primary, and `raStateCard` already handles an
unresolved lens, so the rail renders without a compare control.

**Unverified, and must be checked before implementation:** that each lens's own
resolver tolerates a null primary. If any does not, the correction is to pass
the **candidate set**, never to hand it the first candidate.

### 4.5 · No candidate lost to Local Option dedupe

The exclusion at 28917-28931 exists because `#altResults` would otherwise repeat
the resolved Local Option. In the new architecture the grid is the **canonical
set**, and the lens rail is a separate perspective, so the dedupe is **not
applied to `#ahCandidateGrid` at all**. A product may legitimately appear once as
a candidate and once as a Local Option answer: those are different questions. A
guard asserts every candidate present in the grid regardless of lens state.

### 4.6 · Guidance is untouched

Planning, cost and suitability guidance live in `#hmrPropertyFit`,
`resultsDecide` and `bydClose`, shown affirmatively at 12605-12610 and
independent of any product. They render before and after selection.

---

## 5 · SELECTION BEHAVIOUR

`ahSelectCandidate(code)`:

1. resolves the row by `productCode` from the rendered set — **never by index**
2. renders `buildResultsHero(row)` into `#matchPrimary` and un-hides it
3. populates the four lead-specific sections from that row (4.3)
4. sets `aria-expanded` / `aria-current` on the chosen card; all other cards keep
   peer styling
5. moves focus to the panel heading, with a "Back to all four" control returning
   focus to the originating card
6. deselecting restores the no-selection state — no candidate is sticky, so a
   return visit never finds one pre-chosen

What the panel delivers, all from the existing hero: full product facts, both
price configurations with VAT basis and commercial terms, authorised imagery with
credit and link-back, the governed explanation, the known and open evidence lists.

**Deliberately not built here:** a dedicated Option Detail page (tasks JC-2 to
JC-5, still pending). That is separate approved work and does not belong inside a
presentation correction.

---

## 6 · LAYOUT

**Desktop, 900px and above.** Property assessment, then the heading and the
two-sentence explanation, then the cards in one grid:
`repeat(auto-fit, minmax(300px, 1fr))` — the shipped `#altResults` rule (8626),
which resolves to 2x2 inside the 910px panel and would become 4-across only if
the panel widened. Identical card width, 4/3 media, and type scale (org 11px,
name 19.5px, price 13.5px). Selecting one opens its detail panel immediately
below the grid; the lens rail and "Before you decide" follow unchanged.

**Mobile, 390px.** Single column, `grid-template-columns:1fr` (7104) — stacked
cards of equal height, 4/3 media uncropped. The 80px hero name leaves the first
viewport entirely, so every candidate is reachable in roughly the scroll distance
that previously showed one. The detail panel opens full-width in place, with
"Back to all four" as a persistent control rather than a browser-back dependency.

**Breakpoints to measure:** 1440 / 1280 / 1024 / 900 / 768 / 430 / 390 / 360.
Acceptance: card bounding boxes within 1px at every width, no horizontal page
scroll, every tap target 44px or larger (the J3-4 standard this file holds).

---

## 7 · REGRESSION CONTRACT

New suite, `atlas-tools/prove-no-lead-equality.mjs`:

| | assertion |
|---|---|
| E1 | at no-lead, `#ahCandidateGrid` holds exactly `n` cards |
| E2 | the codes are 425, 437, 457, 523 — catalogue order, no sort introduced |
| E3 | no card carries a preferred or recommended marker; `ctx.isPreferred` false on all |
| E4 | `#matchPrimary` is empty and hidden until a selection is made |
| E5 | `leadResult` is null at no-lead and **`originalRecommendation` is never set** |
| E6 | **no candidate removed by Local Option dedupe** — all present with the lens resolved to each in turn |
| E7 | with a genuine lead, `#ahCandidateSet` is hidden and the hero markup is byte-identical to today |
| E8 | with `use === 'garden-room'`, the new section never appears, whatever the lead state |
| E9 | selecting each candidate in turn yields that candidate's own name, org, price configurations, VAT basis, terms, explanation and imagery — no cross-contamination |
| E10 | Wanderlust's three images, the `(c) BIOBUILDS` credit and link-back present; no AI illustration on any card (P7 re-run) |
| E11 | imageless candidates render the placeholder, never an empty box |
| E12 | the lens rail renders with a null primary; Local Option, Best European and the state cards all reachable |
| E13 | **capability**: the pre-change path still produces 1 hero plus 3 cards, so the suite can tell the architectures apart |
| E14 | geometry at the eight widths in section 6 |

Plus the existing sweep, all of which must stay green: BIOBUILDS acceptance
20/20, publication gate and its capability proof 14/14,
`prove-candidate-lead-honoured.mjs` 16/16, provenance P1-P11, image-rights scan
and self-test, imagery, containment, founder exception, landmarks,
results-configurations, price-presentation-unchanged, the four Python suites, and
the **Garden Room Results baseline captured via `?review=results` before and
after**, compared as the proof that journey did not move.

### Rollback

Three layers. The bounded builder's `--revert` with its `.bak-` sidecar restores
`your-plot.html` byte for byte. The change is one shipped file, so
`git checkout -- your-plot.html` is a complete undo before commit. And because
`#ahCandidateSet` is gated on `pnNoLead`, setting that expression to `false`
disables the entire new architecture at runtime without removing code. The
artefact is never written, so there is no data rollback to need.

---

## 8 · FILES THE IMPLEMENTATION WILL TOUCH

| file | change |
|---|---|
| `your-plot.html` | markup: one new section (~12 lines). JS: `pnNoLead` and `leadResult` threaded through 10 call sites, `ahCandidateCard`, `ahSelectCandidate`, four section populators, `data-rail-run` rekey. CSS: one scoped block. Plus the stale comment at 17314 (below). Estimated +220 / -12. |
| `atlas-tools/build-no-lead-equality.py` | new bounded builder: exactly-once anchors, `--check` / `--revert`, `.bak-noleadeq` sidecar, byte-identity reverse check, per-`<script>` syntax check, refuses if `pnCandidateSplit`, `pnResidentialCandidateList`, `publicVisibility`, `class3a`, `qualification`, `.sort(`, `BIOBUILDS` or `leadWrap.hidden` counts move, hashes the artefact before and after |
| `atlas-tools/prove-no-lead-equality.mjs` | new, E1-E14 |
| this record | amended on implementation with the measured result |

**Not touched:** `additional-home-universe-v1.json`, the generator,
`additional_home_qualification.py`, `image-rights-records.json`,
`image-provenance-records.json`, every other Discovery page, Airtable, the
catalogue.

---

## 9 · OPEN ITEMS CARRIED INTO IMPLEMENTATION

1. **A stale comment, no live defect.** `your-plot.html:17314` asserts "every
   candidate carries governed imagery, so there is nothing to float." That is
   false as of the 11 October regeneration — one of four candidates carries
   imagery. `pnApplyPresentationPriority` is retired with zero call sites, so
   nothing misbehaves, but the comment states something untrue about the current
   data and should be corrected in the same pass.
2. **Lens resolvers against a null primary** (4.4) — unverified, and the first
   thing to measure.
3. **The shared-renderer risk, named rather than minimised.** This touches
   `renderMatchResults`, the shared Results renderer for the live Garden Room
   journey. The `pnResidential` gates are the existing containment pattern, and
   E8 plus the before/after Garden Room baseline are how containment is proved.
   The risk is not zero: this is the largest change to that function since the
   one-renderer correction, and the live journey runs through it.
4. **AH-DIFF-001** — compare universes by Airtable record id, not Product Code.
   Raised during the catalogue preservation check, where ten recoded Luxury
   Garden Studios records read as 10 removals plus 10 additions.
