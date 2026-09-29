# PlotNua Journey Contract

**Authoritative.** This document, not chat memory, is what the repository knows about its own
architecture. Where this document and an implementation disagree, this document is the
specification and the implementation is the defect.

- Enforced by: `atlas-tools/validate-journey-contract.js` (guards J01–J12, M01, P01)
- Guard-capability proof: `atlas-tools/prove-journey-contract.mjs`
- Recorded against: `your-plot.html` at `3099d8d`
- Established: 29 September 2026, by the post-reconciliation stabilisation pass

---

## 1 · The canonical journey

```
DISCOVER → ATLAS → MATCH → RESULTS → MY PLOT → COMPARE → RESOLVE → PROGRESS
                                                        → SUPPLIER / PROVIDER → TRANSACTION
```

Not every homeowner visits every optional screen. **But a later-stage capability must never
silently bypass an earlier stage that owns the relevant decision work.**

The rule that gives this document its reason to exist:

> **SUPPLIER HANDOFF IS NOT OWNED BY OPTION DETAIL.**
> Supplier/provider handoff belongs after the appropriate Resolve / Progress readiness process.
> The supplier handoff is the END of PlotNua's decision journey. It is not the next step after
> seeing a result.

---

## 2 · Status vocabulary

Six terms, and they are not interchangeable. **Hidden is not nonexistent.**

| Term | Meaning |
|---|---|
| **BUILT** | The code exists: screen, model, renderer. |
| **WIRED** | An entry point calls it. The path from a user action to the screen is complete. |
| **VISIBLE** | A homeowner can actually reach it in the shipped build. |
| **DORMANT** | BUILT and WIRED, but its entry control is hidden. Reversible by named restore condition. |
| **BLOCKED** | Cannot be made VISIBLE because a non-code dependency (usually evidence) is absent. |
| **RETIRED** | Deliberately removed. Only this term licenses deletion. |

**DORMANT and BLOCKED code must not be deleted, and must not be re-created in parallel.**
Rebuilding a dormant stage under a new name is the failure mode this contract exists to prevent.

---

## 3 · Stage register

### RESULTS

- **Purpose** — present the publishable pool; name a Best match; open each option.
- **Owner** — `buildResultsHero()`, `buildResultsGalleryCard()`, `buildSaveActions()`, `#screen-match-results`
- **Entry** — completion of Match with a decision profile.
- **Exit** — Option Detail (View option), or Save to My Plot.
- **State owned** — the ranked, gated candidate set for this session. No persistence.
- **Allowed next** — OPTION DETAIL · MY PLOT
- **Prohibited** — Results must not carry an outward supplier link. Results must not make a
  readiness claim.
- **Status** — **VISIBLE**

### OPTION DETAIL

- **Purpose** — let the homeowner understand ONE option properly: governed imagery, product
  facts, why PlotNua showed it, property-specific intelligence, what is not yet known.
- **Owner** — `openProductDetail(productId, returnScreen)`, `#screen-product-detail`,
  `productDetailReturn` (instance of `createReturnableOverlay`)
- **Entry** — Results (View option); My Plot.
- **Exit** — back to the entry screen; Save to My Plot; **continuation into the canonical next
  stage**.
- **State owned** — **none.** Option Detail is a reading surface. It renders state; it does not
  own any.
- **Allowed next** — RESULTS (back) · MY PLOT
- **Prohibited bypasses**
  - Option Detail **may not own or duplicate the Resolve uncertainty model**.
  - Option Detail **may not hold the supplier handoff.** A supplier URL existing is not a reason
    to send the homeowner away.
  - Option Detail **may not assert readiness**; readiness is Progress's to state.
- **Status** — **VISIBLE** (reachable from Results since `3099d8d`)
- **Known violations** — see §5. Two of the three 3099d8d non-canonical items live here.

### MY PLOT

- **Purpose** — hold saved possibilities; the hub every later stage is entered from.
- **Owner** — `#screen-my-plot`, `myPlotRead()`/`myPlotWrite()`, `MYPLOT_SCHEMA`,
  `renderMyPlotPickOne()`, `renderMyPlotPickTwo()`
- **Entry** — Save, from Results or Option Detail; direct navigation.
- **Exit** — Compare · Resolve · Progress · back to Results.
- **State owned** — the saved set, saved journeys, **and the homeowner's Resolve positions**
  (`resolve: resolvePositions.get(id)`, written additively into the My Plot record).
- **Allowed next** — COMPARE · RESOLVE · PROGRESS · RESULTS · OPTION DETAIL
- **Prohibited** — My Plot must retain all three seams even while Resolve and Progress are
  DORMANT. Hiding a button must not remove the wiring behind it.
- **Status** — **VISIBLE**

### COMPARE

- **Purpose** — put two saved options side by side. Compare never picks; the homeowner picks first.
- **Owner** — `compareShortlist()`, `renderMyPlotPickTwo()`, `openCompareScreen()`,
  `closeCompareScreen()`, `resolveCompareCells()`, `COMPARE_FIELDS`
- **Entry** — My Plot, at 2+ saved items (`myPlotCompareBtn.hidden = total < 2`).
- **Exit** — back to My Plot; Option Detail for either side.
- **State owned** — the transient considered pair. Deliberately not persisted.
- **Allowed next** — MY PLOT · OPTION DETAIL · RESOLVE
- **Status** — **VISIBLE**

### RESOLVE

- **Purpose** — deal with what is not yet known about a chosen option: surface what Atlas already
  holds, ask the homeowner only what only they can answer, name PlotNua's own evidence gaps
  honestly, and record a position on each.
- **Owner** — `RESOLVE_REGISTRY` (13 entries), `resolveUncertaintiesFor()`, `resolveEntryState()`,
  `resolveReadiness()`, `renderResolve()`, `openResolveScreen()`, `#screen-resolve`
- **Entry** — My Plot → `myPlotResolveBtn` → `renderMyPlotPickOne(…, openResolveScreen)`.
  Threshold is **ONE** saved item, not two.
- **Exit** — back to My Plot; forward to Progress.
- **State owned** — **the unresolved-decision state, and its persistence.** `resolvePositions`,
  `recordResolveAnswer()`, `recordResolveAcceptance()`, `withdrawResolvePosition()`; persisted
  through the My Plot record.
- **Allowed next** — MY PLOT · PROGRESS
- **Status** — **BUILT · WIRED · DORMANT BY FOUNDER DECISION**
- **Blocker** — ISSUE 007. Founder review rejected the customer-facing Resolve screen for launch.
  Engine, registry, renderer, storage all untouched and still running; only the reveal is withdrawn.
- **Restore condition** — founder decision. Mechanically:
  `els.myPlotResolveBtn.hidden = total < 1;` at the site currently reading `= true`.

**`RESOLVE_REGISTRY` is the canonical uncertainty taxonomy.** Every entry carries `owner`,
`resolvability` and `consequence`. No second uncertainty model may be introduced.

| key | owner | consequence |
|---|---|---|
| contractingEntity | atlas | costly |
| origin | atlas | tolerable |
| leadTime | atlas | costly |
| warranty | atlas | costly |
| access | homeowner | blocking |
| ground | homeowner | costly |
| power | property | tolerable |
| water | property | tolerable |
| priceIncludes | plotnua | costly |
| installationCharges | plotnua | costly |
| afterSales | plotnua | costly |
| planning | world | blocking |
| schedule | plotnua | tolerable |

`resolvability` ∈ `now` · `not-yet`. `consequence` ∈ `blocking` · `costly` · `tolerable`.

### PROGRESS

- **Purpose** — state what has been established, what remains open, and whether the option is
  ready to take further.
- **Owner** — `PROGRESS_REGISTRY`, `PROGRESS_LANES` (maker-stated / what usually happens),
  `progressFor()`, `renderProgress()`, `openProgressScreen()`, `#screen-progress`,
  `window.__pnProgressScreen`
- **Entry** — My Plot → `myPlotProgressBtn` → `renderMyPlotPickOne(…, openProgressScreen)`.
- **Exit** — back to My Plot; **supplier/provider handoff**.
- **State owned** — **readiness and progression state.**
- **Allowed next** — MY PLOT · SUPPLIER / PROVIDER
- **Status** — **BUILT · WIRED · DORMANT BY EVIDENCE BLOCKER**
- **Blocker** — LAUNCH-INT-002. Progress cannot answer its own question until Atlas holds process
  evidence. Market lane answered **0/37**. A stage that can only say what it does not know is
  honest but not ready to be offered.
- **Restore condition** — process evidence in Atlas, then founder decision. Mechanically:
  `total < 1` at the site currently reading `= true`.

Progress owns the sentence `PROGRESS_SITUATION`:
*"From here on, most of it happens between you and the maker."* That sentence marks the boundary
of PlotNua's decision work. **It belongs at the end of Progress and nowhere earlier.**

### ENQUIRY / DISPATCH

**Found by guard J10 during this stabilisation pass, not by the reconciliation that preceded it.**
The reconciliation report said PlotNua had "a link, not a dispatch route". That was wrong: the
dispatch route is built. It is test-gated, which is not the same as absent.

- **Purpose** — compose the Brief and let the homeowner send it to the supplier.
  *Composed by PlotNua, sent by the homeowner* — the L2 Dispatch element of
  `PROGRESS-LAUNCH-ARCHITECTURE.md`.
- **Owner** — `openEnquiryScreen(org, product)`, `closeEnquiryScreen()`, `enquiryRender()`,
  `enquiryComposeMessage()`, `enquiryPayload()`, `enquirySubmit()`, `#screen-enquiry`
- **Entry** — **`?enquiry=test` only.** `ENQUIRY_TEST_MODE` is read from the query string;
  `window.PLOTNUA_OPEN_TEST_ENQUIRY()` is the sole caller, and it is defined only in that mode.
  The code's own words: *"The ONLY route to this screen today."*
- **Exit** — back to the entry screen; submit.
- **State owned** — the composed enquiry, transiently. Submission goes to one dedicated endpoint,
  gated on `ENQUIRY_TEST_MODE` **inside `enquirySubmit()` as well as by the route**, so the
  transport cannot outlive the route it was built for.
- **Allowed next** — the stage it was entered from.
- **Status** — **BUILT · TEST-GATED · BLOCKED BY AT-1**
- **Blocker** — **AT-1**, not the UI. The screen composes a message and can post it; what is
  missing is a supplier address to send it to (email 0/5, telephone 0/5, contact URL 0/5). The
  screen carries a visible `Test mode — not forwarded to a supplier` flag for exactly this reason.
- **Restore condition** — supplier contact evidence in Atlas (AT-1), then a founder decision on
  the live endpoint. **Do not build a second enquiry composer.**

### SUPPLIER / PROVIDER

- **Purpose** — hand the homeowner to the supplier, once PlotNua has completed the decision work
  it can perform.
- **Owner** — `pnSupplierHandover(product, action)` — the **single outbound door**, and the seam
  for the future tracked server-side redirect.
- **Entry** — **Progress**, at sufficient readiness. (Currently entered from Option Detail — a
  recorded violation, §5.)
- **Exit** — the supplier's own site, in a new tab.
- **State owned** — none today. Tracking is designed, not built.
- **Allowed next** — TRANSACTION (off-platform)
- **Prohibited bypasses**
  - **No stage earlier than Progress may introduce a supplier handoff** without an explicit
    exception recorded in this document.
  - `window.open(` must appear **exactly once** in `your-plot.html`, inside `pnSupplierHandover()`.
  - PlotNua must not claim to request a quote, send an enquiry, start a purchase, or track a
    handoff until each is actually built.
- **Status** — **BUILT · MISPLACED** — the function is sound; its call site is too early.
- **Blocker** — **AT-1.** Measured across all 5 suppliers: email 0/5, telephone 0/5,
  contact/enquiry URL 0/5; homepage 5/5; postal `contractingEntity` 5/5, shown nowhere.
  `mailto:` appears 0 times. PlotNua does not know how to reach a single supplier it recommends —
  not by policy, by absence. Until AT-1 closes, the ENQUIRY / DISPATCH stage above cannot be
  taken out of test mode: it has a composer and a transport, but no address to send to.

### TRANSACTION

- **Purpose** — the purchase.
- **Owner** — **the supplier. Not PlotNua.**
- **State owned** — none. PlotNua holds no order, payment, or fulfilment state.
- **Status** — **NOT BUILT, BY DESIGN**
- **Commercial position (Power Sheds, recorded, unchanged)** — PlotNua does the discovery and
  decision work; the customer purchases directly from the supplier; supplier workload minimal;
  **no commission currently agreed; no exclusivity; no sales promise**; tracked server-side
  handover planned, not built. No downstream sale may be claimed without evidence.

---

## 4 · Test classes

An implementation is **not complete** unless all three pass.

| Class | Question | Instruments |
|---|---|---|
| **A · FEATURE** | Does the new functionality work? | the change's own builder guards + capability proof |
| **B · GOVERNANCE** | Do rights, evidence, claims and publication rules still hold? | `validate-image-rights.js`, `prove-results-publication-gate.mjs`, claim-firewall scans |
| **C · JOURNEY** | Has the wider PlotNua journey been preserved? | `validate-journey-contract.js` |

Class C is new, and it is the class that `3099d8d` would have failed.

---

## 5 · Recorded violations — `3099d8d`

`3099d8d` is **not reverted** by this pass. It is recorded, fingerprinted, and frozen: the guards
fail if any of these grows, spreads, or is joined by another of its kind.

| Item | Verdict |
|---|---|
| Results → Option Detail reachability | **KEEP** — canonical |
| Governed Option Detail image rendering | **KEEP** — canonical |
| `pnOpenQuestions()` parallel uncertainty model | **NON-CANONICAL · V1** |
| Option Detail → supplier handoff | **NON-CANONICAL · V2** |
| `pnSupplierHandover()` single-door function | **REUSABLE · placed too early · V3** |
| `"[Supplier] has not published a price for this one."` | **NON-CANONICAL · V4** |

**V1 — `pnOpenQuestions()` duplicates `RESOLVE_REGISTRY`.** Verified: it contains zero references
to `RESOLVE_REGISTRY`. Its six questions map almost one-for-one onto registry entries
(VAT→`priceIncludes`, base→`ground`, install→`installationCharges`, planning→`planning`,
delivery→`deliversHere`, cost→`priceIncludes`), but carry no owner, no resolvability, no
consequence, no state and **no persistence**. Frozen at **7** declared questions (6 render for any one product; the cost question is price-conditional).

**V2 — Option Detail holds the outward CTA.** `pnSupplierHandover(product, nextAction.state)` is
called from `openProductDetail`'s "Take this further" section, seven stages early.

**V3 — `pnNextAction()` gates on URL existence, not readiness.** `resolveReadiness(states)` exists
and nothing in Option Detail calls it.

**V4 — an Atlas gap stated as a supplier fact.** See §7.

---

## 6 · Market source-of-truth invariant

> **MARKET-SPECIFIC SOURCE OF TRUTH MUST MATCH THE HOMEOWNER MARKET.**

An Irish homeowner journey must not silently present a non-Irish product URL or a non-euro price
as though it were the Irish supplier route, when a verified Irish storefront exists.

**Recorded risk — Power Sheds.** Atlas holds:

| Product | Price | URL |
|---|---|---|
| 12x12 Apex Classic Log Cabin | 4864 **GBP** | `powersheds.com/products/apex-classic-log-cabin-44mm` |
| 14x14 Apex Classic Log Cabin | 5634 **GBP** | `powersheds.com/products/apex-classic-log-cabin-44mm` |
| 16x12 Apex Log Cabin | 7444 **GBP** | `powersheds.com/products/apex-log-cabin` |

All three are `priceEvidenceState: verified` and all three resolve to next-action **State A**
("See price at Power Sheds"). The supplier operates a dedicated Irish storefront at
**`ie.powersheds.com`**, publishing in **euro**, founder-confirmed visually.

So PlotNua is positioned to tell an Irish homeowner "See price at Power Sheds" and send them to a
**UK** URL with a **sterling** figure behind it. This is a territory and currency mismatch on the
one supplier in the pilot.

**Not fixed in this pass** — prices are not corrected here, and the active temporary
**15% off all log cabins** promotion (ending 1 October 2026) **must not be ingested as standing
price evidence**. The absence of a durable euro price is precisely why no euro price is held.

Guard **M01** records the mismatch and fails if any code asserts the UK route *is* the Irish
supplier route.

---

## 7 · Price semantics — the PB046 distinction

> **NO PRICE DATA ≠ THE SUPPLIER HAS NOT PUBLISHED A PRICE.**

This distinction predates the reconciliation and is already correct in the display layer
(`your-plot.html`, PB046 block):

| Constant | Text | Means |
|---|---|---|
| `PB046_NO_PRICE` | `Price not published` | Atlas holds no price evidence |
| `PB046_AMBIGUOUS_PRICE` | `Price not confirmed` | Atlas holds evidence it cannot rank |
| `PB046_QUOTE_PRICE` | `Priced on enquiry` | evidenced quote-only |

The code's own note: collapsing these *"would convert an honest inability to choose into a false
claim about the maker."*

**V4 breaks it.** `pnNextAction()` State B emits
`org + ' has not published a price for this one.'` — a factual claim about supplier publication
behaviour, derived from an Atlas evidence gap. Guard **P01** forbids that sentence shape unless
supplier-publication absence is itself evidenced. Suitable replacement wording must follow PlotNua
writing governance; *"PlotNua does not currently hold a confirmed price for this option"* is the
kind of thing that is true, but is not prescribed here.

---

## 8 · Build protocol — binding

**Before adding any new screen, route, CTA, next-action resolver, or supplier handoff:**

1. **Search this document** for the stage the capability belongs to.
2. **Search the code** for an existing screen or function already serving that stage.
3. **Identify the canonical owner** from §3.
4. **Extend the existing architecture** where it fits.
5. **Prove why a new path is needed** if no existing path fits — in writing, in the change's own
   record, before the code is written.
6. **Run all three test classes** (§4). Class C is not optional.

> **"I did not know it existed" is no longer an available justification.**
> It was the justification for `3099d8d`, and this document is the reason it cannot be used again.

---

## 9 · Founder decisions still open

These are recorded as open. **They must not be made silently by an implementation pass.**

**A · RESOLVE.** Founder review rejected the customer-facing Resolve screen for launch. The later
decision is: restore as-is, redesign, or expose its intelligence through another experience.

**B · PROGRESS.** Hidden because market/process evidence was 0/37. Evidence work must come before
any readiness decision.

**C · SUPPLIER CONTACT / DISPATCH.** AT-1 remains open. The Enquiry screen is built and
test-gated; what is missing is supplier contact evidence, not a composer. PlotNua must not
describe the enquiry route as live while it is gated at `?enquiry=test`.
