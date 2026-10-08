# DISC-025 V2 HOMEOWNER EXPERIENCE — FREEZE RECORD

**Status:** VISUALLY FROZEN — founder acceptance PASS, 8 October 2026
**Scope:** homeowner-facing presentation only
**Authority:** founder visual verdict after real 390px review, then final polish, then PASS
**Register state:** **CLOSED.** This record does **not** authorise opening it.

---

## 1 · What was accepted

| | |
|---|---|
| Opening | "Could a corner of your garden work for somebody else?" |
| Questions | unchanged — the visual reference for V2 |
| Result headline | "A corner of your garden could work" |
| Result body | three derived **WHY IT COULD WORK** reasons, no bordered report card, no exposed posture |
| Demoted | "A few things worth thinking about" · "Worth knowing — see what we checked" · "How would this work?" — all collapsed |
| Invitation | immediately after the reasons: "If somebody nearby needed a corner, would you want to know?" |
| CTA | "Yes — let me know" |
| Caveat | "This is a register, not a match. We may never find anybody near you." — visible, below the CTA |
| Form | one privacy line; "Anything else we should know?" |
| Success | simplified, ends after register / privately kept / we email and ask first / not a match / how to leave |
| My Plot | moved below the interest journey |
| Demand language | **conditional only** |

The intermediate explanatory sentence under the headline was **removed**, not reworded: the three observations explain the headline.

---

## 2 · Frozen artefacts

| File | SHA-256 |
|---|---|
| `disc025-borrowed-garden-check.html` | `df54fd5e3405d6551f925d94d3df6e5a3a5b0254e7d2353da91b6950cb9c2fd6` |
| `atlas-tools/build-g3-garden-interest.py` | `f156f9978ad4a9fb…` |
| `worker/garden-register/src/index.js` | `66ee90e2d94968ee59a1f2c71674956735b1f593c1d4ef7a97b77f477e177c79` — **UNCHANGED** |

Applied by two bounded builders, each refusing any input but the exact expected hash, each idempotent:
`atlas-tools/build-disc025-v2-experience.py` · `atlas-tools/build-disc025-v2-polish.py`

---

## 3 · G29 — the presentation-derivation guard

The V2 result shows a tick list rather than the engine's raw reason bullets. Two of those ticks have **no reason key behind them**: the engine emits a reason only when a dimension is a *problem*, so "a way in that is not the house" and "you keep using the garden" are derived from the frozen answers. G29 exists to close that risk.

**Canonical enumeration, from the engine's own `combinations()` helper:**

| | |
|---|---|
| Combinations | **240** = 3 × 5 × 4 × 4 |
| Early exits (`no_garden`) | **48** |
| **Assessments** | **192** |
| By posture | OPEN 8 · CONDITIONAL 94 · PENDING 90 |

An earlier specification said "108". **That figure was a guess and was wrong.** `G29pre` and `G29pre2` now assert the measured counts from the engine, so the number can never again be stated from memory.

**The rule, as frozen:** a tick appears only where the frozen answer qualifies **and** the engine has not flagged that dimension; a flagged dimension renders the engine's own reason, never a tick; **PENDING renders no ticks at all**; `tenure` is absent from the tick vocabulary entirely, so an ownership tick is impossible by construction.

**G29 assertions — 7, all PASS**

```
G29pre   240 combinations from the engine
G29pre2  48 early exits / 192 assessments, measured not assumed
G29      every rendered tick is an approved sentence
G29a     PENDING never renders a positive tick
G29b     a dimension flagged by the engine never renders a tick
G29c     the tick set is exactly the frozen-input derivation, all 192
G29d     an early exit renders no ticks at all
```

**G29c is the load-bearing one.** The approved rule is **restated independently inside the test** and compared element-by-element across all 192. If the page ever invents a rule of its own the two disagree. A guard that imported the page's own table could not detect that.

### Mutation capability — proven, not assumed

| Mutation | Caught by |
|---|---|
| `tenure` re-added to the tick list | G29 + G29c (34 offenders) |
| PENDING short-circuit removed | G29a + G29c (78) |
| a flagged `way_in` made to tick | G29b + G29c (30) |
| derivation condition weakened to emit an unsupported positive | G29b (48) + G29c (94) |
| tick list removed entirely | G29c (94) |

**One mutation attempt was rejected rather than counted.** Removing the `TICK_OK` check alone changed nothing, because `TICK_COPY` holds only qualifying keys — a **vacuous** mutation. It was rewritten until it genuinely emitted an unsupported positive, and then it was caught.

---

## 4 · Suite totals at freeze

| Suite | Result |
|---|---|
| `prove-guards.mjs` | **74 passed, 0 failed** |
| `prove-g3.mjs` | **179 passed, 0 failed** |
| `prove-tenure-invariance.mjs` | **10 passed, 0 failed** |
| `prove-g3-mutations.mjs` | **27 caught, 0 blind, vacuous or crashed** |
| `prove-worker-mutations.mjs` | **3 caught, 0 blind, vacuous or partial** |

---

## 5 · Contract invariants — all verified at freeze

| | |
|---|---|
| Garden consent SHA-256 | `85c436084349e841017171ef12e2c0d5e28fa24a82d99f4c2beaca8f6eee9b9c` |
| Page ↔ Worker garden consent | **byte-identical** |
| Grower consent SHA-256 | `32ba8b3ec621ed6e15edf0cc4c4fe95bec7b386d9c95179737fe9179990148f1` |
| `PRIVACY_VERSION` | `2026-10-PHASE2-V2` |
| Four question texts | 4 of 4 unchanged |
| Frozen option values | **31 of 31** unchanged |
| Governed `CONTEXT_COPY` | **7 of 7** unchanged |
| `intPayload()` | all 16 fields present, unchanged |
| `garden_note` field id / name / payload key | unchanged |
| Funnel events | 2 of 2 unchanged |
| Worker | **untouched** |
| `WRITES_ENABLED` | **false** |
| `EMAIL_ENABLED` | **false** |
| `INTEREST_PUBLIC` | **false** |

### Airtable at freeze — verified by direct read

Gardens **0** · Growers **0** · Status log **0** · Consent proofs **0** · Incidents **0**

**No row was created by this release.** No submission, synthetic or genuine, was made. No write window was opened.

---

## 6 · "PRIVATE PREVIEW · NOT PUBLIC" — proven preview-gated

The badge is governed by the **switch**, not the query string:

```js
if (!INTEREST_PUBLIC) $('bgIntPrev').hidden = false;
```

Proven at runtime against a **copy** with `INTEREST_PUBLIC = true` — the production switch was never touched:

| Page | Query | Badge |
|---|---|---|
| `INTEREST_PUBLIC = true` (simulated public) | none | **HIDDEN** |
| `INTEREST_PUBLIC = true` (simulated public) | `?interest=preview` | **HIDDEN** |
| `INTEREST_PUBLIC = false` (production) | `?interest=preview` | VISIBLE |
| `INTEREST_PUBLIC = false` (production) | none | SECTION ABSENT |

**The badge cannot render in the ordinary public path.** Even with the preview query present, a public page keeps it hidden — the gate is the switch, so publication removes the badge automatically with no further edit required. The fourth row also re-confirms the containment that has held since G3: with no query and the switch false, the whole section is **removed from the DOM**, not merely hidden.

---

## 7 · What this record does NOT authorise

- **It does not open the homeowner register.** `INTEREST_PUBLIC` stays `false`.
- **It does not open writes.** `WRITES_ENABLED` stays `false`.
- **It does not enable email.** `EMAIL_ENABLED` stays `false`; the Worker has no mail adapter.
- **G7 remains BLOCKED** pending the insurer / broker prerequisite. Introduction eligibility must continue to exclude `buying`, absent tenure and unconfirmed tenure.
- **R0 — `hello@plotnua.ie` receipt — remains outstanding** and must PASS before genuine registrations are accepted. It is the only erasure route; the Worker has none.
- **G6 remains PASS and closed.** The browser-path integration proof stands; this release changed presentation only and did not touch the proven path.

---

## 8 · Known limitation of the visual acceptance

Acceptance was given on the analytics-free 390px harness, in which **Google Fonts is stripped**. Hierarchy, spacing, rhythm, wrapping and layout were judged faithfully; the **typeface was not**. Final typographic judgement belongs on the live page after deployment.

---

## 9 · Closure

The DISC-025 V2 homeowner experience is **visually frozen**. No further copy, spacing, styling or UX change is authorised without a new founder decision.

**Public registration remains CLOSED.**
