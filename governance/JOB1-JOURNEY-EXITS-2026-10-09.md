# JOB 1 · P0 JOURNEY EXITS

**Date:** 9 October 2026
**Status:** **FOUNDER VISUAL ACCEPTANCE — PASS, 9 October 2026. RELEASED.**
**Authority:** founder ruling, 9 October 2026, on global site chrome outside a
governed Property Check decision experience

---

## 0 · FOUNDER VISUAL ACCEPTANCE — PASS

Given 9 October 2026 after inspection of the review pack
(`JOB1-JOURNEY-EXITS-REVIEW.zip`: twelve real renders of the exact candidate
files at desktop-1440 and mobile-390, the complete candidate diff, both bounded
builders, both mutation harnesses and the governance records).

| Decision | Verdict |
|---|---|
| Journey Exit footer, desktop **and** mobile | **APPROVED** |
| DISC-025 — new site chrome visibly outside the frozen homeowner experience | **APPROVED**; the append-only post-freeze amendment is preserved exactly as designed |
| 404 Search pill, at its settled full-opacity state | **APPROVED** |

### Two items parked by founder decision, not fixed in Job 1

**`disc026-power-station.html` desktop alignment — PARKED.** Measured at 1440px
across all ten checks: nine journeys begin their content at x=208 against the
footer container's x=180 — about 4px apart once the footer's own 24px padding is
counted, so effectively aligned. `disc026-power-station.html` begins at **x=361**,
a **181px** delta. This is that page's own container geometry, not the footer's,
and it is **pre-existing and page-specific**. Recorded here as a parked styling
issue. **It is not a Job 1 release blocker and was deliberately not fixed.**

**Google Fonts in the capture environment — NOT A RELEASE BLOCKER.** The webfont
request returns HTTP 407 from the capture proxy, so Fraunces and Work Sans fell
back to Georgia and system-ui in the review renders. Hierarchy, spacing, rhythm,
wrapping, colour, alignment and the frozen-experience boundary are faithful; the
**typeface is not**. The caveat is preserved and **no typography change was
made**, in line with §8 of the V2 freeze record.
**Scope:** Job 1 only. No analytics events, no performance work, no
accessibility programme, no source/served split, no comment stripping.

---

## 1 · The founder ruling, and the boundary it draws

Adding global site chrome / onward navigation **outside** a governed Property
Check decision experience is permitted and does not reopen the frozen engine or
homeowner experience.

Every Property Check has the same shape, and exactly one `</main>`:

```
<header class="XX-top"> … </header>
<main class="XX-wrap">   THE GOVERNED DECISION EXPERIENCE   </main>
<script>                 THE ENGINE                        </script>
```

**The boundary is that `</main>`.** One canonical region is spliced immediately
after it. For DISC-025, the `<main>` element *is* the frozen V2 check / result /
interest experience, so proving that element byte-identical is the whole of the
ruling's condition.

| The ruling requires | Proven by |
|---|---|
| no question / option / engine / result / evidence change | E6 — `<main>` byte-identical on all ten, against the page on disk |
| no consent / privacy change | Worker `git diff` EMPTY; `prove-g3.mjs` G4/G4b/G4c/G4d/G11 PASS |
| no interest / register change | E6; `intPayload()` byte-identical; E13 forbids any register invitation in the region |
| no payload change | `intPayload()` byte-identical before vs after |
| no switch change | `INTEREST_PUBLIC = false` unchanged in page; `WRITES_ENABLED` / `EMAIL_ENABLED` are Worker env and the Worker is byte-identical |
| no existing CTA semantics weakened | E9 — every pre-existing anchor, href **and** its text, still present on all ten |
| no frozen internal layout/copy changed to accommodate the addition | E4 prose identical; E3 inline `<style>`/`<script>` bodies identical; E2 every byte outside the splice identical; `<head>` never touched |

---

## 2 · What was built

### 2.1 `PLOTNUA JOURNEY EXIT v1` — the ten Property Checks

A `<footer class="pnx">` with an `<h2>`, three onward routes, a labelled
`<nav>`, and the contact line. One canonical region, sha256
`83dcd3f1418a1b797d94b3707097b23b760738a0c88388c4d477f88d39e03469`, **byte-identical
on all ten pages** (E1).

| Route | Destination |
|---|---|
| Explore the Discovery Library | `discoveries.html` |
| Search PlotNua | `search.html` |
| My Plot | `your-plot.html` |
| Home · About · Contact · Privacy · Terms | the ordinary global set |

`discoveries.html` is the canonical "explore everything" destination, matching
`index.html`'s own footer (LAUNCH-INT-002, restored). The Discovery pages' older
footers still point at `index.html#discover`; that inconsistency is **recorded,
not fixed here**.

**Deliberate exclusions.** No script of any kind (E7). No external asset (E8) —
in particular `search.css`, `search.js` and the `.pns-` Search pill are **not**
brought onto journey pages, because `build-search-rail.py`'s own R6 excludes
Property Checks by design and overriding that is a separate founder decision.
No count of Discoveries is printed, because a number in site chrome goes stale
the day a Discovery ships. No demand, matching, registration, pricing or
earnings claim, and no sign-up invitation (E13) — the register is CLOSED and
this is navigation, not an offer.

**CSS scope.** Every selector begins `.pnx` (E11). `pnx-` appears nowhere else
in the repository. The five brand custom properties used are defined
**identically** in all ten checks' `:root`, measured not assumed (E0d):
`--accent #4F6B4A` · `--ink #1F3B2E` · `--line rgba(31,59,46,.12)` ·
`--paper #F8F5EC` · `--soft #55605A`. Both brand typefaces already load on all
ten. The region carries its own `<style>` in the body so that no `<head>` and
no frozen inline stylesheet is touched.

### 2.2 Search on the 404

The 404 was the one reachable page on the site with no route to Search. Cause,
measured: `build-search-rail.py` derives its page list from `sitemap.xml`, and
the 404 is deliberately not in the sitemap. Nothing about the page excluded it —
it carries exactly one `<a class="brand-mark">` and the `.brand-mark.in` fade
mechanism, which is the rail's majority variant.

The region is **copied from `index.html`, not authored** (F2, F3), so the 404's
Search entry is byte-identical to the one already shipping on 19 pages
(`0b7f22d248698550`), and cannot drift. `build-search-rail.py` is **not
modified and not re-run**; its own `--check` still passes. `sitemap.xml` is
untouched and the 404 remains unlisted (F7) and `noindex` (F8). The 404's hero,
copy, Discovery carousel and footer are byte-identical (F5), and all 20
pre-existing anchors survive (F6).

### 2.3 One Search V1 census guard raised, deliberately

`prove-search-acceptance.mjs` H12b asserted `19 faded + 2 nofade = 21 public
surfaces`. **It fired, and it was right to** — that is exactly what a scope
census is for.

Search V1's markup, CSS, JS and behaviour are unchanged: H12a independently
proves the 404's pill hashes to the approved faded variant byte for byte. Only
the *number of surfaces carrying it* changed, by one, under founder
authorisation. The assertion was therefore raised and kept exact, naming the
extra surface, and a second assertion `H12b2` pins that the twentieth faded
surface is `404.html` specifically — so the census still cannot drift silently.

**This is the one place where Job 1 edited a Search V1 artefact, and it needs
founder ratification.** The alternatives were to leave the suite failing or to
revert the 404, neither of which is better.

---

## 3 · The CTA-less Discoveries — I WAS WRONG, and nothing should change

The whole-site audit reported three published Discoveries as having "no call to
action at all": `discovery-garden-retreat.html`,
`discovery-above-and-beyond.html`, `discovery-your-home-on-screen.html`.

**That finding was false, and the instrument was wrong.** It counted anchors
carrying a button-ish class. Pattern C Discoveries deliberately forbid button
chrome — their own stylesheet says so: *"One quiet text route into the Property
Check. Deliberately NOT a filled button: Pattern C forbids button chrome in this
section."* Measuring for buttons on pages designed without buttons was never
going to find anything.

Re-audited individually, each already does the honest thing:

| Discovery | What it actually has |
|---|---|
| **Garden Retreat** | A "This property check is being prepared" panel saying plainly that PlotNua is building a check, that *"It is not ready, and nothing on this page assesses your property"* — then: Explore *What Could You Build in Your Garden?* → Explore *Above and Beyond* → See all Discoveries → Back to the homepage |
| **Your Home On Screen** | The same pattern: the check is being prepared and says so → Explore *Driveway Income* → Explore *Home Exchange* → See all Discoveries → Back to the homepage |
| **Above and Beyond** | A complete **in-page** journey, *"Find what could work for you"* — four questions, a result with closest matches, ready-made vs designed-to-order routes, supplier links, a bespoke route, Change an answer / Start again, and an honest "About this check". One of the most complete pages on the site. |

All three also carry the search rail, the footer, `your-plot.html`,
`discoveries.html` and `search.html`.

**Decision: no change to any of the three. There is no CTA gap and no product
gap at the CTA level.** The two "being prepared" panels are the correct handling
of a Discovery whose check does not exist — exactly what the founder's
instruction ("report a product gap rather than inventing a misleading CTA") was
protecting, already built. Routing Garden Retreat or Above and Beyond into the
Garden Room recommender, as the audit loosely suggested, would have replaced an
honest statement with a misleading one.

---

## 4 · Before / after journey-exit census

Computed by the builder (E14), not asserted. Columns: `discoveries.html` /
`search.html` / `your-plot.html` / `index.html`.

| Check | before | after |
|---|---|---|
| `disc005-home-exchange.html` | `..DD` | `DDDD` |
| `disc014-driveway-income.html` | `..DD` | `DDDD` |
| `disc022-hidden-cars-check.html` | `..DD` | `DDDD` |
| `disc023-buy-original-irish-art.html` | `..DD` | `DDDD` |
| `disc024-open-your-home-to-art.html` | `..DD` | `DDDD` |
| `disc025-borrowed-garden-check.html` | `..DD` | `DDDD` |
| `disc026-compute-readiness-check.html` | `..DD` | `DDDD` |
| **`disc026-power-station.html`** | **`..D.`** | `DDDD` |
| `disc027-neighbourhood-parcel-house.html` | `..DD` | `DDDD` |
| `disc029-hidden-bins-check.html` | `..DD` | `DDDD` |

`disc026-power-station.html` was the worst case and was not in the original
audit: alone among the ten it has no header mark anchor, so it had **no link
home at all** — only My Plot and the compute-readiness check. The footer fixes
that as a side effect; its header is left alone.

**404.html:** Search route — before: **absent**. After: present.

---

## 5 · Guards and their capability proof

A guard that has never been seen to fail is not a guard.

### `build-journey-exit.py` — 14 guard families, 19 mutation cases

```
19 caught · 0 blind · 0 vacuous · 0 wrong guard
```

Guard order: `E0b E0c E0d E0e → E1 → E6b → E5 → E9 → E14 → E12 → E4 → E6 → E3 → E2 → E7 E8 E11 E13`.

Specific guards run before general ones so each has an **independently
reachable** failure, and the catch-all byte guard E2 runs last.

| Mutation | Caught by |
|---|---|
| region made page-dependent | E1 |
| region spliced inside `<main>` | E6b |
| region injected twice | E5 |
| existing My Plot CTA neutered | E9 |
| Search destination swapped away | E14 |
| labelled `<nav>` downgraded to `<div>` | E12 |
| editorial prose reworded | E4 |
| bytes changed inside `<main>` | E6 |
| region brings a `<script>` | E3 |
| a pre-existing inline `<script>` altered | E3 |
| a byte changed outside the splice point | E2 |
| storage API named in the region | E7 |
| `search.css` pulled onto a journey | E8 |
| unscoped `footer a` selector added | E11 |
| misleading register invitation added | E13 |
| a second `</main>` added | E0b |
| page already uses the `pnx-` prefix | E0c |
| a required brand token renamed | E0d |
| page differs from its frozen baseline | E0e |

### `build-404-search.py` — 11 guards, 12 mutation cases

```
12 caught · 0 blind · 0 vacuous · 0 wrong guard
```

Order `F0 F1 F2 F2b → F3 → F5 → F6 → F7 → F8 → F4 → F9 → F10`, for the same
reason: F4 (every byte outside) was claiming three failures that F5, F6 and F8
describe better.

### The updated Search V1 census

`H12b` and `H12b2` were both proven capable of failing, by stripping the Search
region off the 404 in an isolated copy: both FAIL, suite exits 1.

### Three defects the mutation proof found in my own work

These are recorded because they are the reason the proof exists.

1. **Three guards went BLIND.** E2, E6 and E3 compared the builder's own
   intermediate (`base`) against its output. A builder that corrupts `base`
   before deriving `out` makes that comparison trivially pass. **Fixed:** all
   three now re-read the page **from disk** at guard time, which a defective
   builder cannot launder. This is a genuine strengthening, not a test tweak.
2. **Five guards were misattributed.** E6b, E4, E9, E14 and E5 were each
   subsumed by a more general guard that ran earlier, so none of them could be
   shown to fire on its own. **Fixed** by ordering specific before general. The
   same happened three times in the 404 builder and was fixed the same way.
3. **Two mutations were silent no-ops** and were reported as BLIND guards.
   `SPLICE + '.replace(...)'` binds the call to the final operand `base[i:]`,
   not to the whole expression, so the mutation only ever touched the tail after
   `</main>`. **Fixed**, and the vacuity check was strengthened: a mutant that
   the builder lets through is now rebuilt with guards neutralised and its
   output compared to the control's, so a mutation that changed nothing is
   reported as VACUOUS rather than crediting a guard for catching nothing.

Also fixed: `strip_region` now absorbs the leading newline, so a region spliced
at the wrong offset is reported by the boundary guard (E6b) rather than leaving
a stray newline for the byte guard (E2) to claim.

---

## 6 · Suites — before and after

| Suite | Before | After |
|---|---|---|
| `prove-guards.mjs` | 74 passed, 0 failed | **74 passed, 0 failed** |
| `prove-g3.mjs` | 179 passed, 0 failed | **179 passed, 0 failed** |
| `prove-tenure-invariance.mjs` | 10 passed, 0 failed | **10 passed, 0 failed** |
| `prove-g3-mutations.mjs` | 27 caught, 0 blind/vacuous/crashed | **27 caught, 0 blind/vacuous/crashed** |
| `prove-worker-mutations.mjs` | 3 caught, 0 blind/vacuous/partial | **3 caught, 0 blind/vacuous/partial** |
| `validate-journey-contract.js` | 85 checks run | **85 checks run** |
| `prove-search-acceptance.mjs` | 148 passed, 0 failed | **149 passed, 0 failed** (H12b raised, H12b2 added) |
| `prove-search-guards.py` | rc=0 | **rc=0** |
| `build-search-rail.py --check` | rc=0 | **rc=0** — the rail builder is untouched and still agrees with its 21 pages |
| `prove-discovery-library-images.mjs` | rc=0 | **rc=0** |
| `prove-disc026-discovery.mjs` | **rc=1 — ALREADY FAILING** | rc=1, identical failure |

**The one pre-existing failure, stated plainly.** `prove-disc026-discovery.mjs`
fails on `G5 . NO REMOTE IMAGERY — UNKNOWN FAILS CLOSED → FAIL exactly five
SVGs`, on `discovery-house-as-power-station.html`. It failed **before** Job 1
touched anything, it is an SVG count on a Discovery page, and it has nothing to
do with journey exits. It is **not fixed here** — Job 1 is Job 1 — and is
recorded as an open item.

---

## 7 · Changed paths, and hashes

Every change is **insertions only** except the one test file, where two census
lines were replaced:

```
24  0  404.html
70  0  disc005-home-exchange.html
70  0  disc014-driveway-income.html
70  0  disc022-hidden-cars-check.html
70  0  disc023-buy-original-irish-art.html
70  0  disc024-open-your-home-to-art.html
70  0  disc025-borrowed-garden-check.html
70  0  disc026-compute-readiness-check.html
70  0  disc026-power-station.html
70  0  disc027-neighbourhood-parcel-house.html
70  0  disc029-hidden-bins-check.html
24  2  atlas-tools/prove-search-acceptance.mjs
```

New files: `atlas-tools/build-journey-exit.py` ·
`atlas-tools/prove-journey-exit-mutations.py` ·
`atlas-tools/build-404-search.py` · `atlas-tools/prove-404-search-mutations.py` ·
`atlas-tools/journey-exit-baseline.json` ·
`atlas-tools/404-search-baseline.json` · this record.

### Whole-file hashes, and the `<main>` that did not move

| File | file sha before | file sha after | `<main>` sha — **unchanged** |
|---|---|---|---|
| `disc005-home-exchange.html` | `d56058696f50` | `5b78ee811fa5` | `626ab81b6743` |
| `disc014-driveway-income.html` | `e850cbfc77f4` | `10120f16f68a` | `08171aa6fbad` |
| `disc022-hidden-cars-check.html` | `90dcca2a06e6` | `ad6b5cd3044b` | `66aa6a194851` |
| `disc023-buy-original-irish-art.html` | `f86b30b71ec4` | `fc68aa8fa21e` | `a770d9cf6683` |
| `disc024-open-your-home-to-art.html` | `ba3ab4f8ca95` | `8f9bf0521046` | `c254a5c91a31` |
| `disc025-borrowed-garden-check.html` | `df54fd5e3405` | `12e442393b13` | `05bf977f0d4f` |
| `disc026-compute-readiness-check.html` | `bf36de261ec2` | `e0c0b1336b75` | `699040f1c674` |
| `disc026-power-station.html` | `ebc0eddc7bbc` | `8273c9db53d6` | `405f4537030f` |
| `disc027-neighbourhood-parcel-house.html` | `d2c3ead7b0bf` | `285e3a1dd36b` | `c72d85c21fce` |
| `disc029-hidden-bins-check.html` | `e9c857555f7c` | `525ab68ee20b` | `7763a2a65b5d` |
| `404.html` | `97c83162cdaa` | `48ed52028c67` | — (no `<main>`) |

`worker/garden-register/src/index.js` —
`66ee90e2d94968ee59a1f2c71674956735b1f593c1d4ef7a97b77f477e177c79` —
**UNCHANGED**, `git diff` empty.

### The DISC-025 freeze record needs amending

`DISC-025-V2-EXPERIENCE-FREEZE-RECORD.md` §2 pins
`disc025-borrowed-garden-check.html` at `df54fd5e3405…`. The whole-file hash is
now `12e442393b13…`. **The frozen V2 experience itself did not change** — its
`<main>` is byte-identical at `05bf977f0d4f` — but the record's hash is stale
and must be amended by a dated post-freeze note, in the same convention as
`G1B-V2-AMENDMENT-2026-10-08.md`: amend, never rewrite. **Not done in this
record** — it is a founder decision whether the amendment is made now or at
acceptance.

---

## 8 · What this record does NOT do

- **It does not open the homeowner register.** `INTEREST_PUBLIC` stays `false`,
  `WRITES_ENABLED` stays `false`, `EMAIL_ENABLED` stays `false`.
- **It does not add the proposed analytics events.** Job 2 is not authorised.
- **It does not touch performance or accessibility as a programme.** Job 3 is
  not authorised. The region happens to be correct markup — a real `<footer>`
  with one labelled `<nav>`, an `<h2>` and visible focus rings — but no skip
  link was added and no landmark was repaired anywhere else.
- **It introduces no source/served split and strips no comments.**
- **It does not change any Discovery page.** The three audited Discoveries were
  found already correct.
- **It does not fix the Discovery footers' `index.html#discover` vs
  `discoveries.html` inconsistency**, or the pre-existing
  `prove-disc026-discovery.mjs` failure, or the parked
  `disc026-power-station.html` alignment. All three are recorded as open and
  **none was fixed opportunistically.**

---

## 9 · Open items carried out of Job 1

| Item | Status |
|---|---|
| `prove-disc026-discovery.mjs` G5 "exactly five SVGs" | **Failing before Job 1 began**, identical after. An SVG count on `discovery-house-as-power-station.html`, unrelated to journey exits. Not touched. |
| `disc026-power-station.html` 181px content offset vs the footer | **PARKED** by founder decision, 9 October 2026 |
| Discovery-page footers link `index.html#discover`; `index.html`'s own footer links `discoveries.html` | Recorded, not fixed |
| Analytics funnel blind spots (`discovery_view`, `search_performed`, `search_result_opened`) | **Job 2 — not authorised, not begun** |
| My Plot page weight, alt text, landmarks | **Job 3 — not authorised, not begun** |
