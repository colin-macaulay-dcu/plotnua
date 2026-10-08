# PRE-G5 CORRECTION PLAN — BOUNDED, TWO CHANGES ONLY

**Status:** PLAN ONLY · 8 October 2026 · nothing executed
**Authority:** founder decisions D-G5-1 = **OPTION 1 (G1B is authoritative)**,
D-G5-2 = **option i**, D-G5-3 = **YES**, recorded 8 October 2026.
**Purpose:** align the implementation with the already-frozen G1B §5 contract,
and make the deployed proof suite safe to run with writes on. Nothing else.

Base state this plan starts from and must return to, unchanged except where
named:

| | |
|---|---|
| production commit | `057bb81` |
| page sha256 | `bd08ce67d004a8b24be00bc50e75a31bcf18693dd5e9dfb6974267917e327c19` (140,738 B) |
| Worker sha256 | `4c5a47831ec85178f083f4535f1bbb732ee9c4542af43f28ef8b88105897a3ba` (21,293 B) |
| switches | `INTEREST_PUBLIC = false` · `WRITES_ENABLED = "false"` · `EMAIL_ENABLED = "false"` |
| Airtable | five tables × 0 records |

**Scope discipline.** This correction removes one condition from three page
sites and one Worker site, and splits one test file. It adds no feature, no
question, no field, no copy the founder has not approved, and no behaviour for
`own`, for `rent`, or for absent tenure. **If a step appears to require more
than that, it stops** (see STOP conditions).

---

## 1 · EXACT FILES AND REGIONS REQUIRING CHANGE

### Change A — buying-tenure contract alignment

| # | file | line | region | what |
|---|---|---|---|---|
| A1 | `disc025-borrowed-garden-check.html` | **2666** | `g3-js` | `intPaintTenure()` — the condition that shows the permission block |
| A2 | same | **2708** | `g3-js` | `intPayload()` — the condition that attaches `permission_confirmed` |
| A3 | same | **2734** | `g3-js` | `intLocalProblem()` — the condition that requires tick + note |
| A4 | `worker/garden-register/src/index.js` | **336** | `handleGarden` | the server-side tenure refusal block |

All three page sites sit inside the frozen **g3-js** region (lines
**2461–2842**, `/* PLOTNUA-G3-INTEREST-BEGIN` → `/* PLOTNUA-G3-INTEREST-END */`).

**Regions that must stay byte-identical, and provably can:**

| region | lines | why untouched |
|---|---|---|
| certified engine | 1201–1461 | `decide()` is not involved; tenure is read from `answers`, which the engine already produced |
| `PlotNuaJourneySave` | — | shared byte-for-byte with four other journeys |
| **g3-html** | 1028–1176 | the `#bgIntCond` markup (1101–1107), the checkbox, the label and the note field **all stay exactly as they are**. Only the JS that shows or hides them changes |
| g3-css | — | no style change |

So the diff is confined to one frozen region out of five, and that is the single
strongest claim this correction can make. **Any change to g3-html, g3-css, the
engine or the save band means the correction has overreached.**

### Change B — deployed-proof suite correction

| # | file | what |
|---|---|---|
| B1 | `worker/garden-register/test/prove-deployed.mjs` | **split**: keep D3–D13 (switch-independent); remove D1/D2; correct the false header statement |
| B2 | `worker/garden-register/test/prove-deployed-switch.mjs` | **new**: D1/D2 only, with an explicit expected-mode argument |

No product file is touched by Change B.

### A hazard specific to the builder

Lines **2708** and **2734** contain the **identical** string
`if (answers.tenure && answers.tenure !== 'own') {`. A bounded builder that
anchors on that line alone will match twice and must refuse. Each anchor must
include the following line to be unique:

```
2708  …!== 'own') {  +  "      body.permission_confirmed = $('bgIntPerm').checked === true;"
2734  …!== 'own') {  +  "      if (!$('bgIntPerm').checked) return 'permission_confirmed';"
```

The builder asserts **exactly-once** occurrence for each widened anchor, as
every prior PlotNua builder does.

---

## 2 · EXACT OLD → NEW VALIDATION LOGIC

### A1 · `intPaintTenure()`, page line 2666

```js
/* old */  if (tenure === 'rent' || tenure === 'buying') {
/* new */  if (tenure === 'rent') {
```

The `else` branch is unchanged and already correct for the new case: it hides
`#bgIntCond` and sets the note hint to `Optional.` — which is exactly what
G1B §5 specifies for `buying`.

The comment above it changes from the general tenure rule to name the
distinction, so the next reader does not "fix" it back:

```js
/* G1B §5 TENURE RULE, as frozen. `rent` is the only tenure that needs
   somebody else's agreement before PlotNua could ever introduce anyone, so
   `rent` is the only tenure that shows this block. `buying` is STORABLE with
   no permission and no statement — and remains non-promotable, which is a G7
   decision and not a form control. */
```

### A2 · `intPayload()`, page line 2708

```js
/* old */  if (answers.tenure && answers.tenure !== 'own') {
/* new */  if (answers.tenure === 'rent') {
             body.permission_confirmed = $('bgIntPerm').checked === true;
           }
```

Note the simplification is deliberate: `answers.tenure === 'rent'` is already
falsy-safe, so the `answers.tenure &&` guard is redundant and removing it
leaves no behaviour behind.

### A3 · `intLocalProblem()`, page line 2734

```js
/* old */  if (answers.tenure && answers.tenure !== 'own') {
             if (!$('bgIntPerm').checked) return 'permission_confirmed';
             if ($('bgIntNote').value.trim().length < 20) return 'garden_note';
           }
/* new */  if (answers.tenure === 'rent') {
             if (!$('bgIntPerm').checked) return 'permission_confirmed';
             if ($('bgIntNote').value.trim().length < 20) return 'garden_note';
           }
```

### A4 · Worker `handleGarden`, line 336

```js
/* old */  if (tenure !== 'own') {
             if (!permission_confirmed) return REFUSED(cors, 'permission_confirmed');
             if (!note || note.length < 20) return REFUSED(cors, 'garden_note');
           }
/* new */  if (tenure === 'rent') {
             if (!permission_confirmed) return REFUSED(cors, 'permission_confirmed');
             if (!note || note.length < 20) return REFUSED(cors, 'garden_note');
           }
```

The existing comment is rewritten, because its current last sentence — *"Storage
is still permitted — this refusal exists only because a submission with neither
has nothing to review"* — is the reasoning that produced the divergence, and it
does not hold for `buying`:

```js
/* G1B §5 TENURE RULE, as frozen. `rent` may reach an introduction ONLY with
   explicit permission, so `rent` alone requires the tick AND the homeowner's
   own statement. `buying` is storable with neither, is never promoted, and
   `own` needs ordinary confirmation only. PlotNua never asks for a deed, a
   lease or a landlord's details: the homeowner's own sentence is evidence of
   what they said, not of the fact. Non-promotion is enforced at G7, which is
   BLOCKED — it is not, and must not become, a form control. */
```

**Four lines of logic change in total.** Everything else in both files is
comment or test.

### Deliberately NOT changed

```js
line 328  if (!tenure) return REFUSED(cors, 'inherited_tenure');
```

Absent tenure keeps refusing. Per founder instruction it stays as a documented
contract/code divergence, unreachable through the homeowner journey because
`decide()` only runs once every question is answered. **The builder asserts this
line is still present and unaltered afterwards** — a positive guard that the
correction did not drift into the second divergence.

---

## 3 · DO HOMEOWNER-VISIBLE FORM FIELDS CHANGE FOR BUYING?

**No field is added, removed, renamed or re-labelled. The markup does not
change at all.**

What changes is **visibility and requirement** for one tenure:

| homeowner answered | `#bgIntCond` (tick + hint) | `garden_note` | before | after |
|---|---|---|---|---|
| `own` | hidden | optional | — | **unchanged** |
| `rent` | shown, tick required | required, ≥20 chars | — | **unchanged** |
| `buying` | **shown, tick required** | **required, ≥20 chars** | | **hidden, not required** · optional note |

The `buying` homeowner now sees **the same form an owner sees**: name, email,
district, water, size, timing, an optional free-text box labelled "Anything you
want to tell us", and the single consent tick.

**No new sentence is written.** The smallest correct change is the removal of a
condition, and the recommendation is to add nothing — because every
homeowner-visible sentence on this page is founder-owned, and because G1B's
clarifying-question rule for `buying` is explicitly left unchanged by this
correction, so there is nothing yet to tell them.

**One founder copy option, if wanted, not recommended for this correction.** A
single non-blocking line to a `buying` homeowner, something like *"You told us
you are buying this home. We will keep what you have told us and come back to
you when the sale is done."* It is defensible and arguably kinder. It is also
new founder-owned copy, it edges toward the clarifying-question rule this
correction is not touching, and it would make the diff a copy change as well as
a logic change. **Recommendation: no copy change now.** If the founder wants
it, it should be its own bounded pass after this one lands.

---

## 4 · HOW THE BUYING PATH SHOULD LOOK TO THE HOMEOWNER

End to end, after the correction:

1. Property Check, question 1: they answer **"buying"**.
2. They finish the remaining questions and reach their result as today —
   `decide()` is untouched, so the result is byte-for-byte the same result they
   get now.
3. The invitation appears (unless `spare_corner === 'no_garden'`, founder
   decision Q1, unchanged).
4. They open the form and see **the owner's form**: no permission tick, no
   "somebody else has to agree" hint, the note box marked *Optional*.
5. They submit. The Worker accepts it (writes permitting) and stores
   `inherited_tenure: 'buying'` with no `permission_confirmed` and no
   `garden_note` unless they chose to write one.
6. They see the standing `received` state: *"You're on the register"*, with the
   out-of-pilot sentence if their district is outside the four, and the
   email-to-withdraw route.

**What they are not told, and must not be:** that a match is coming, that
anyone is looking, or that being on the register leads anywhere. The existing
no-promise wording is unchanged and is asserted unchanged (§8).

**What the correction does not give them:** promotion. A `buying` record is
stored and never introduced. Nothing in the codebase introduces anybody — G7
does not exist and is BLOCKED — so non-promotion needs no code today. It needs
a **governance entry**, added by this plan to the G7 prerequisites: *when
introduction logic is built, `inherited_tenure === 'buying'` must be excluded
from the introducible set, as must absent and unconfirmed tenure.* That is the
one place the obligation can actually be discharged, and recording it now is
how this correction avoids trading a storage bug for an introduction bug later.

---

## 5 · PAYLOAD DIFFERENCES FOR own / rent / buying

Fields the page sends, after the correction. Unchanged rows are marked.

| field | `own` | `rent` | `buying` |
|---|---|---|---|
| `first_name`, `email`, `district`, `water`, `size_note`, `timing` | always | always | always *(unchanged)* |
| `over_18` | `true` | `true` | `true` *(unchanged)* |
| `consent_text` | frozen sentence | frozen sentence | frozen sentence *(unchanged)* |
| `source` | `garden_interest` | `garden_interest` | `garden_interest` *(unchanged)* |
| `inherited_tenure` | `own` | `rent` | `buying` *(unchanged)* |
| `inherited_spare_corner`, `inherited_way_in`, `inherited_your_own_use` | always | always | always *(unchanged)* |
| `inherited_result_key` | if available | if available | if available *(unchanged)* |
| `garden_note` | only if typed | **required**, ≥20 chars | **only if typed** ← changed |
| `permission_confirmed` | **absent** | `true` | **absent** ← changed |

Exactly **two cells change**, both in the `buying` column:

- `permission_confirmed` goes from `true`/`false` to **absent** — matching
  `own`, which the frozen suite already asserts is *absent, not false* (G12b).
- `garden_note` goes from required to optional.

`own` and `rent` payloads are **byte-identical** before and after. That is
testable and must be tested (§7, T5).

---

## 6 · WORKER VALIDATION DIFFERENCES

Refusal order after the correction — only rows 10 and 11 change, and only for
one tenure:

| order | condition | `own` | `rent` | `buying` | absent |
|---|---|---|---|---|---|
| 1 | consent text not configured | `not_open` | `not_open` | `not_open` | `not_open` |
| 2–7 | `first_name` · `email` · `district` · `water` · `size_note` · `timing` | refused by field | same | same | same |
| 8 | `inherited_tenure` not in `own/rent/buying` or absent | — | — | — | **`refused · inherited_tenure`** *(unchanged, documented divergence)* |
| 9 | `over_18 !== true` (strict) | `refused · over_18` | same | same | — |
| 10 | no `permission_confirmed` | not applied | `refused · permission_confirmed` | **not applied** ← changed | — |
| 11 | `garden_note` < 20 chars | not applied | `refused · garden_note` | **not applied** ← changed | — |
| 12 | consent hash mismatch | `refused · consent_text` | same | same | — |
| 13 | `!writesEnabled(env)` | `not_open` | `not_open` | `not_open` | — |
| 14 | Airtable error | `unavailable` | same | same | — |

Everything else is untouched: the closed vocabularies, `typecast:false`, the
exact-Origin CORS check, the Fetch Metadata checks, `emailKeyExists()`
idempotency, the three-table write, the consent hash, the reply shapes.

`permission_confirmed` is still read (`body.permission_confirmed === true`) and
still written when truthy, so a hand-POSTed `buying` submission that carries a
tick stores it. That is truthful — it records what was sent — and removing it
would be a second change for no gain.

---

## 7 · TESTS THAT MUST BE CHANGED OR ADDED

### 7A · Assertions that must INVERT (they currently assert the divergence)

| suite | assertion | now | after |
|---|---|---|---|
| `prove-guards.mjs` | **G34c** "buying with NO permission tick is refused" → `refused · permission_confirmed` | passes | **must invert** → passes validation and is stopped only by the switch (`503 not_open`), the same shape as G34a for `own` |
| `prove-g3.mjs` | **G8 / G8b / G8c / G8d / G8e** run in a loop over `['rent', 'buying']` — asserting the block is shown, the tick names "the current owner", and the note "becomes required" | pass for both | **the loop must drop `buying`**; those five keep running for `rent` only |

Nothing else in the frozen suites asserts the old `buying` behaviour. `prove-g3.mjs`
G7/G7b (`own`: block hidden, note optional) are unchanged and become the model
for the new `buying` assertions.

### 7B · Assertions that must be ADDED

| id | suite | assertion |
|---|---|---|
| T1 | `prove-g3.mjs` | `buying`: `#bgIntCond` is **hidden** |
| T2 | `prove-g3.mjs` | `buying`: the note hint reads *Optional* |
| T3 | `prove-g3.mjs` | `buying`: a submission with **no tick and no note** is sent — `sent.length === 1`, and the page does not block it |
| T4 | `prove-g3.mjs` | `buying`: `permission_confirmed` is **absent from the payload, not false** (the G12b pattern) |
| T5 | `prove-g3.mjs` | **invariance**: the `own` payload and the `rent` payload are byte-identical to the pre-correction payloads for the same inputs — the only way to prove the correction did not leak |
| T6 | `prove-g3.mjs` | `buying` with a note **under** 20 characters is still sent (the minimum applies to `rent` only) |
| T7 | `prove-guards.mjs` | `buying` **with** a tick and a note is also accepted (stopped only by the switch) — the field is permitted, not forbidden |
| T8 | `prove-guards.mjs` | `rent` refusals **unchanged**: no tick → `permission_confirmed`; tick + 11-char note → `garden_note` (G34b, G35a, G35b re-asserted verbatim) |
| T9 | `prove-guards.mjs` | **absent tenure still refused** → `refused · inherited_tenure` (G35e re-asserted; the documented divergence is deliberately preserved) |
| T10 | `prove-guards.mjs` | no code path sets `status` to anything but `interest_submitted`, and no path treats `buying` as introducible — a textual guard over `src/index.js` with comments stripped |
| T11 | `prove-g3.mjs` | the no-promise wording is still present exactly once, unchanged |

### 7C · Change B — the suite split

`prove-deployed.mjs` becomes **switch-independent only**: D3–D13, eleven
controls, every one of them a refusal that writes nothing in either switch
state. Its header statement is corrected. The present text is false:

> "Every assertion here is a REFUSAL. This script cannot create a record even
> if the Worker were wide open: it sends no valid consent text for a write it
> expects to succeed…"

Both consent strings in that file are **byte-identical** to `CONSENT_TEXT.garden`
and `CONSENT_TEXT.grower`, and both bodies are complete and valid. The replacement
says what is true:

```
 * SWITCH-INDEPENDENT NEGATIVE CONTROLS. Every assertion here is a refusal that
 * holds in BOTH switch states — wrong method, wrong origin, wrong path, wrong
 * Fetch Metadata, preflight. None of them carries a body that could be
 * written, so this file is safe to run with WRITES_ENABLED=true.
 *
 * The two switch-DEPENDENT controls (a valid garden POST and a valid grower
 * POST, which return 503 not_open with writes off and 200 received with writes
 * on, creating a record) live in prove-deployed-switch.mjs and are NOT here.
 * Corrected 8 October 2026: this file previously claimed it could not create a
 * record, and carried two valid bodies that could.
```

`prove-deployed-switch.mjs` (new) holds D1 and D2 and takes a required mode
argument:

```
node test/prove-deployed-switch.mjs <base-url> --expect-closed   # asserts 503 not_open, writes nothing
node test/prove-deployed-switch.mjs <base-url> --expect-open     # asserts 200 received, AND WRITES TWO RECORDS
```

It **refuses to run without the flag** — no default. `--expect-open` prints, before
it posts, the exact addresses it will write (`deployprobe@example.com`,
`deployprobe2@example.com`) and the three tables each will touch, so the two
rows are planned rather than discovered. Those addresses should also move to the
`@plotnua.invalid` convention, since `example.com` is not controlled by PlotNua
and the rows hold the address in clear.

### 7D · Suites that must be re-run unchanged

`prove-g3-mutations.mjs`, `prove-g3-deployed.mjs`, `prove-g3-review-harness.mjs`
— see §8 for the one mutation that needs re-anchoring.

---

## 8 · MUTATION AND GUARD-CAPABILITY REQUIREMENTS

### 8A · Builder guard capability — every guard proven able to fail

Two builders are needed, each with its own capability proof in the established
pattern (`prove-g3-builder-guards.py`, 25/25):

- `build-g1b-tenure-alignment.py` — the three page sites
- `build-worker-tenure-alignment.py` — the one Worker site

Guards each builder must carry, and each must be **demonstrated capable of
firing** against a deliberately broken input:

| # | guard |
|---|---|
| 1 | base sha256 is exactly `bd08ce67…` (page) / `4c5a4783…` (Worker) — refuse to patch an unexpected file |
| 2 | each widened anchor occurs **exactly once** (the 2708/2734 collision above) |
| 3 | not re-runnable over its own output — refuse if the new text is already present |
| 4 | engine region byte-identical after |
| 5 | save region byte-identical after |
| 6 | **g3-html region byte-identical after** — the markup must not move |
| 7 | **g3-css region byte-identical after** |
| 8 | everything outside the g3-js region byte-identical after |
| 9 | `if (!tenure) return REFUSED(cors, 'inherited_tenure');` still present, unaltered (the preserved divergence) |
| 10 | the `rent` branch body unchanged — both inner refusals still present, in order |
| 11 | no new homeowner-visible string introduced: the set of quoted string literals in the g3-js region is unchanged except inside comments |
| 12 | comments stripped before every textual assertion — **assertion, not mention** |

Guard 12 is not optional. Three of these guards reason about text that also
appears in the comments being rewritten; the recorded failure mode is a guard
firing on its own explanatory comment, and `strip_comments()` is the fix that
was already designed for it.

### 8B · Mutation proof — the existing harness must be re-anchored

`prove-g3-mutations.mjs` **M7** substitutes this exact line:

```js
"    if (tenure === 'rent' || tenure === 'buying') {"
```

After A1 that string no longer exists, so M7 would fail to apply rather than
fail to be caught — the worst outcome, because an unapplied mutation can read
as a pass. **M7 must be re-anchored to `if (tenure === 'rent') {`** and its
label updated.

**M8** anchors on the `length < 20` line inside `intLocalProblem()`. That line
is unchanged in text and only its enclosing condition changes, so M8 should
still apply — but it must be re-verified, not assumed, and the mutation harness
must still report 0 blind.

### 8C · New mutations required

| id | mutation | must be caught by |
|---|---|---|
| M26 | page: `tenure === 'rent'` → `tenure !== 'own'` (reinstate the divergence) | T1/T2/T3 |
| M27 | Worker: `tenure === 'rent'` → `tenure !== 'own'` | T7 / G34c-inverted |
| M28 | page: `answers.tenure === 'rent'` → `true` in `intLocalProblem` (require the tick of everyone, owners included) | G7, T8 |
| M29 | Worker: delete the `rent` branch entirely (relax everything) | T8 |
| M30 | Worker: `if (!tenure) return REFUSED(...)` deleted (silently "resolve" the second divergence) | T9 |

Target: **30/30 caught, 0 blind.** M30 matters most — it is the guard against
this correction quietly growing into the change the founder excluded.

---

## 9 · COMPLETE G3 RE-PROOF REQUIRED

The frozen page is being touched, so G3's freeze is reopened and must be
re-earned in full. Nothing short of the original bar.

| # | proof | expectation |
|---|---|---|
| 1 | `prove-g3.mjs` | **166 → ~172 / 0** (five `buying` assertions retired, T1–T6 + T11 added). Every pre-existing assertion that is not in §7A must pass **unchanged** |
| 2 | `prove-g3-mutations.mjs` | **30 / 30 caught, 0 blind**, with M7 re-anchored and M26–M30 added |
| 3 | `prove-g3-builder-guards.py` | all guards for both new builders proven capable of failing |
| 4 | `prove-guards.mjs` (G2 local Worker) | **65 → ~68 / 0**, with G34c inverted and T7–T10 added |
| 5 | engine region sha256 | **`72c0f466ab4aa198…` — byte-identical** |
| 6 | save region sha256 | **`df88b6e3bef36c4b…` — byte-identical** |
| 7 | **g3-html region sha256** | **`829ff4f63724506c…` — byte-identical** |
| 8 | **g3-css region sha256** | **`b7e873413ceb6dc7…` — byte-identical** |
| 9 | **240 engine outcomes** | **`f59443dce4044f22…` — all 3×5×4×4 identical.** `decide()` is untouched, so every outcome for every combination including all 80 `buying` paths must be unchanged |
| 10 | g3-js region sha256 | **changes** — the only region that may. Record the new value |
| 11 | page sha256 | changes. Record old → new and the byte delta |
| 12 | `node --check` on extracted JS; `node --check` on the Worker | clean |
| 13 | founder visual review | **required at 390px and 1440px for the `buying` state specifically** — the state nobody has yet seen, because it did not exist. `own` and `rent` need no re-review: their DOM is proven identical by T5 and guards 6–8 |
| 14 | `prove-g3-review-harness.mjs` | 46/0, with a `buying` capture added so item 13 has something to look at |
| 15 | `prove-g3-deployed.mjs` | 10/0 against the live page, **after** deployment |

Item 9 is the one to insist on. If any of the 240 outcomes moves, the
correction has reached the engine and must be reverted immediately — a tenure
alignment in a register form cannot change what the Property Check tells
anybody.

**The G3 freeze record must be superseded, not edited in place**, with the
previous hash journey retained: `cf614c4f…` → `86cdf32a…` → `1a20d6ed…` →
`bd08ce67…` → the new value.

---

## 10 · WORKER LOCAL AND DEPLOYED PROOF

**Local, before any deploy:**

1. `node --check src/index.js`
2. `prove-guards.mjs` at the new count, 0 failed — it runs the Worker locally,
   so it proves the source, not the deployment
3. Secret sweep repeated on the modified file: `AIRTABLE_TOKEN` appears only in
   comments and `env` reads
4. Confirm `wrangler.toml` is **unmodified**: `WRITES_ENABLED = "false"`,
   `EMAIL_ENABLED = "false"`, `ORIGIN`, `PRIVACY_VERSION`, `PILOT_DISTRICTS`
   all byte-identical. This correction changes no var

**Deployed, with writes still OFF:**

5. `wrangler deploy` from `worker/garden-register/`. Record the new version id
   beside `ed9d2dc6-69a0-4c88-91f3-9418a0954bc7`
6. Record the new `src/index.js` sha256; it is no longer `4c5a4783…`, and every
   governance document asserting that hash must be updated in the same pass
7. `prove-deployed.mjs` (the corrected, switch-independent eleven) — all pass
8. `prove-deployed-switch.mjs --expect-closed` — both routes `503 not_open`
9. **The decisive new deployed control:** a valid `buying` POST with **no tick
   and no note** must return **`503 not_open`**, not `400 refused ·
   permission_confirmed`. Before the correction it returns the 400. That single
   observation is the whole proof, and it is safe with writes off
10. Positive controls alongside it, so the 503 is the switch and not a
    validator that has stopped working: a `buying` POST with a bad district →
    `400 refused · district`; a `rent` POST with no tick → `400 refused ·
    permission_confirmed`
11. Airtable: five tables × **0 records**, confirmed after every step above

Step 9 plus step 10 together are what G2's live proof established as decisive,
applied to the one behaviour that changed.

---

## 11 · SOURCE-CONTROL AND DEPLOYMENT SEQUENCE

Explicit-path staging throughout. **Never** `git add .`, `git add -A`,
`git commit -a`, never amend published history. Both existing stashes and all
nine unrelated untracked paths left untouched.

Pre-flight: `git fetch`, confirm `origin/main` is still `057bb81`. **If it has
moved, stop and inspect before integrating. Never force-push.**

| # | commit | paths | note |
|---|---|---|---|
| 1 | **test suite correction** | `worker/garden-register/test/prove-deployed.mjs`, `…/prove-deployed-switch.mjs` | D-G5-3. Lands first and independently: it touches no product file, so it can be committed and reviewed before anything with behaviour in it |
| 2 | **builders** | `atlas-tools/build-g1b-tenure-alignment.py`, `atlas-tools/build-worker-tenure-alignment.py`, `atlas-tools/prove-g1b-tenure-builder-guards.py` | the tooling that performs the change, committed before its output, so the output is reproducible from a committed source |
| 3 | **Worker alignment** | `worker/garden-register/src/index.js` | one logic change + comment |
| 4 | **page alignment** | `disc025-borrowed-garden-check.html` | three logic changes + comment, new sha256 in the message |
| 5 | **proof suites** | `worker/garden-register/test/prove-g3.mjs`, `…/prove-guards.mjs`, `…/prove-g3-mutations.mjs`, `…/build-g3-review-harness.py` if the capture changes | the inverted and added assertions |
| 6 | **governance** | `governance/G3-FREEZE-RECORD.md` (superseded), `governance/G1B-BORROWED-GARDEN-CONTRACT.md` (**annotation only** — see below), `governance/G3-PUBLIC-SWITCH-CHECKLIST.md` (the G7 non-promotion obligation), `governance/G5-EXECUTION-PLAN.md` (A4 revised), `governance/PRE-G5-CORRECTION-PLAN.md` (this file, with its execution record) | last, so it records what actually happened |

**G1B is not amended.** D-G5-1 = option 1 means the contract was right and the
code was wrong, so §5 keeps its exact frozen wording. The only permitted touch
is an appended, dated note recording that the implementation was brought into
line on this date, with the four changed sites named. If a step appears to
require changing §5's text, that is option 2 and it was declined — **stop**.

**Deployment order, and it matters:**

1. Commits 1–6 locally. **Nothing pushed.**
2. Full local proof (§9 items 1–12, 14).
3. **Worker deployed first**, with writes off (§10). The Worker is deployed by
   `wrangler`, not by the push, so it is independent of the Pages deployment.
4. Deployed Worker proof (§10 items 7–11) — including step 9.
5. **Founder visual review** of the `buying` state (§9 item 13), from the
   harness capture.
6. Only on founder sign-off: **push `main`**, which is a GitHub Pages native
   branch deployment and publishes the page.
7. `prove-g3-deployed.mjs` 10/0 against the live page; re-confirm the live page
   sha256; re-confirm `INTEREST_PUBLIC = false` in the live source; re-confirm
   five tables × 0.

Worker before page is deliberate. If the page shipped first, a `buying`
homeowner using `?interest=preview` would meet a form that lets them submit
without a tick and a Worker that refuses it — a page/Worker misalignment, which
is precisely the class of fault the single-repo decision (D-A = A) exists to
prevent. The reverse order is safe: the Worker accepts a payload the page is
not yet producing.

---

## 12 · ROLLBACK ROUTE

Every layer has an independent, already-proven route back.

| layer | rollback | proof it worked |
|---|---|---|
| **page, pre-push** | `git reset` the local commits, or re-run nothing at all — `origin/main` still has `057bb81`. Nothing is published until step 6 | live page sha256 still `bd08ce67…` |
| **page, post-push** | a **revert commit** restoring the file to `bd08ce67…`, then push. Never amend, never force-push, never rewrite published history | live page sha256 back to `bd08ce67…`; `prove-g3-deployed.mjs` 10/0 |
| **Worker** | `wrangler rollback` to version `ed9d2dc6-69a0-4c88-91f3-9418a0954bc7`, **or** re-deploy from the committed `4c5a4783…` source. The old source is preserved in commit history, which is exactly what PS-2 was closed to guarantee | deployed sha256 back to `4c5a4783…`; a `buying` POST with no tick returns `400 refused · permission_confirmed` again |
| **test suites** | revert commits 1 and 5 | counts back to 166/0, 65/0, 25/25 |
| **governance** | revert commit 6 | the G3 freeze record reads as it does today |
| **Airtable** | **nothing to roll back.** `WRITES_ENABLED` stays `"false"` for the whole correction; no record is created at any point | five tables × 0 throughout |
| **switches** | nothing to roll back — none is touched | `INTEREST_PUBLIC=false`, `WRITES_ENABLED="false"`, `EMAIL_ENABLED="false"` |

The reason this rollback is cheap is that the correction creates **no data**. It
should be executed before `WRITES_ENABLED` is ever flipped, and this plan is
sequenced that way on purpose: a correction with no records behind it can be
undone completely, and one with records behind it cannot.

---

## 13 · EXACT STOP CONDITIONS

Stop, revert to the base state, and report on **any** of these.

**Scope breaches — the correction is growing beyond its mandate:**

1. **Any of the 240 engine outcomes changes**, or the engine region hash moves.
2. **The g3-html, g3-css or save region hash moves.** The markup and the
   styling do not change; if a step seems to need them to, the approach is
   wrong.
3. **Any change to `own` or `rent` behaviour**, in the page or the Worker —
   T5's payload invariance failing, or any G34b / G35a / G35b / G7 / G7b
   assertion needing an edit.
4. **The absent-tenure refusal is touched.** It stays as the documented
   divergence by founder instruction.
5. **G1B §5's text is changed.** That is option 2 and it was declined.
6. **A new homeowner-visible string appears** that the founder has not
   approved — guard 11 firing.
7. **A new field, question, control or vocabulary value** is required.
8. **Any promotion, matching, eligibility or introduction logic** is required or
   added. Non-promotion is a G7 obligation and a governance entry, not code
   written today.
9. **The change cannot be expressed as removing a condition.** If it needs a new
   branch, a new state or a new function, stop and re-plan.

**Integrity failures:**

10. A builder guard **cannot be made to fire** — an unprovable guard is not a
    guard.
11. The mutation harness reports **any blind mutation**, M30 above all.
12. An anchor does not occur exactly once, or a builder is re-runnable over its
    own output.
13. Either base sha256 does not match (`bd08ce67…` / `4c5a4783…`).
14. `origin/main` has moved from `057bb81`. Inspect; **never force-push**.
15. `wrangler.toml` differs in any byte.
16. `node --check` fails on either file.

**Deployed failures:**

17. **Step 10.9 does not behave**: a valid `buying` POST with no tick and no
    note returns anything other than `503 not_open` with writes off.
18. A positive control stops working — a bad district no longer returns
    `400 refused · district`, which would mean the validator, not the switch,
    has changed.
19. **Any Airtable record exists at any point.** Writes are off for the entire
    correction; a record means something is wrong that this plan did not
    anticipate.
20. `INTEREST_PUBLIC` is found to be anything but `false` in the live page.
21. The deployed Worker sha256 does not match what was just deployed.
22. Founder visual review of the `buying` state is anything but PASS.

---

## STANDING CONSTRAINTS

- **`WRITES_ENABLED` stays `"false"`** for the whole correction.
- **`INTEREST_PUBLIC` stays `false`.** It is not opened, and the `buying` state
  is reviewed through `?interest=preview`.
- **`EMAIL_ENABLED` stays `"false"`.** There is no mail adapter; flipping it
  would not enable email.
- **No Airtable record is written.**
- **G5 is not executed.** This correction precedes it; §A4 of the G5 plan is
  revised by it (the `buying` case becomes a straightforward accepted record
  with no permission evidence, and the §4D arithmetic returns to four Gardens
  rows).
- **No G4. No G7. No email work. No outreach. No acquisition traffic.**
- **PS-1 stays CLOSED.** The footer is not reopened.
- **PS-2 stays CLOSED.** The Worker remains version-controlled under
  `worker/garden-register/`, which is what makes the rollback in §12 possible.
- **PS-3 stays OPEN, scoped to G7 only.** It does not block this correction,
  G5 or G6.
- The absent/unconfirmed-tenure divergence **remains documented and
  unresolved**, by founder instruction.

---

**PLAN ONLY.** No file edited. No switch changed. No deployment. No Airtable
write. The only file written today is this one.
