# G5 PROOF RECORD — PRIVATE CONTROLLED-WRITE AND ERASURE PROOF

**Status:** PASS — private controlled-write and erasure proof complete · 8 October 2026
**Authority:** G1B (FROZEN) · G2 Worker contract · G3 freeze record · PRE-G5 correction (CLOSED)
**Operator:** Colin MacAulay (Cloudflare deploys) with Claude (submissions, Airtable reconciliation)

## 1 · Final state

| | |
|---|---|
| Closed Worker version | `c9de84c8-b480-4f29-b560-737325516d41` |
| `WRITES_ENABLED` | `"false"` |
| `EMAIL_ENABLED` | `"false"` |
| `INTEREST_PUBLIC` | `false` — never flipped |
| `wrangler.toml` | `2a4b5c4cb8839deff581197839f296d0511b4a1e71a5e0cbe77d55ee4cb6ed30` |
| `src/index.js` | `66ee90e2d94968ee59a1f2c71674956735b1f593c1d4ef7a97b77f477e177c79` |
| Five tables | **0 / 0 / 0 / 0 / 0** |

Both hashes match the certified pre-G5 baseline exactly. No application code changed
during G5. The write switch was temporarily changed for each controlled attempt, and
the missing/incorrect Airtable bindings were corrected while the Worker was closed.

## 2 · Three attempts, two aborted

The window opened three times. Both aborts were caught on the first probe, both wrote
nothing, and both are recorded because the failure modes are instructive.

**Attempt 1 — version `0f9505f7-52c6-40dd-b895-99f8e8145586`.** A1 returned
`503 not_open` despite `WRITES_ENABLED="true"`. Cause: **`AIRTABLE_BASE` secret
missing.** `writesEnabled(env)` tests three things — the flag *and* both secrets — so a
missing secret is indistinguishable from a failed flip at the reply. Emergency close
run. Tables confirmed 0.

This is the failure the execution plan predicted and placed at step 1, ahead of the
flag. My read-only preflight command checked wrangler auth and the switches but
**omitted `wrangler secret list`**. That omission is mine and it cost an opened window.

**Attempt 2 — version `f017f433-0c3d-4a13-8ade-bfd1332750e8`.** A1 returned
`503 unavailable · at403`. The switch was now working — `unavailable` comes from
refusal step 14, past `writesEnabled` — so the Worker genuinely attempted the write and
**Airtable refused with HTTP 403**. Cause: the **inherited token lacked access to the
Gardener Register base**. Emergency close run. Tables confirmed 0, no partial write.

**Resolution.** A dedicated `plotnua-garden-register` token now holds
`data.records:read` + `data.records:write`, scoped to the **PlotNua Gardener Register
base only** (`appUie3wPmPITfMW7`). `AIRTABLE_BASE` restored to that base id. Both
confirmed present by `wrangler secret list` before reopening.

**Attempt 3 — version `211ec470-f944-4084-b299-513d8157c33c`.** Complete execution,
below.

## 3 · Accepted cases — exact arithmetic

Baseline before A1: 0/0/0/0/0, five direct reads.

| Case | Response | Gardens | Growers | Status log | Consent proofs | Incidents |
|---|---|---|---|---|---|---|
| A1 `own` / raheny | `200 received` | 1 | 0 | 1 | 1 | 0 |
| A2 `rent` / killester, tick + 65-char note | `200 received` | 2 | 0 | 2 | 2 | 0 |
| A3 `own` / elsewhere_in_dublin | `200 received` | 3 | 0 | 3 | 3 | 0 |
| **A4 `buying` / donnycarney** | `200 received` | 4 | 0 | 4 | 4 | 0 |
| **A5 duplicate `email_key`** | `200 received` | **4** | 0 | **4** | **4** | 0 |
| A6 grower / raheny | `200 received` | 4 | **1** | **5** | **5** | 0 |

Reconciled by direct Airtable read after **every** case. Final accepted state matched
the contract exactly: **Gardens 4 · Growers 1 · Status log 5 · Consent proofs 5 ·
Incidents 0.**

Every Gardens row carried `status = interest_submitted`, `privacy_version =
2026-10-PHASE2-V1`, `source = garden_interest`, `over_18 = true`. Every status-log row:
`from_status` empty string, `to_status = interest_submitted`, `actor = system`,
`reason = submission_accepted`, `record_ref` matching the subject row id. No prohibited
field appeared on any row.

## 4 · A4 — `buying` accepted without permission evidence

`inherited_tenure: buying`, **no `permission_confirmed`, no `garden_note`** in the
payload. Accepted. The stored row carries neither field.

This is the PRE-G5 correction working as intended: FROZEN G1B §5 makes `buying`
storable with no permission condition, and the implementation — which had been stricter
than the contract — now matches it. A willing homeowner mid-purchase is no longer
refused.

## 5 · A5 — same-table `email_key` idempotency

The duplicate key is **`email_key`: the submitted email address lower-cased
(`email.toLowerCase()`), compared within one table.** Not a postal address; the register
collects none.

A5 submitted `G5-A1@PlotNua.Invalid` — A1's address in mixed case — to the **same garden
route**, deliberately carrying *different* district (`artane`), water (`none`) and size
(`not_sure`) so that any row created would be instantly distinguishable.

Result: **zero rows added to any table**, and the homeowner still saw `200 received`.
Beyond that, **A1's row was not overwritten** — still raheny / outside_tap / small. The
short-circuit returns before all three creates:

```js
if (await emailKeyExists(env, table, emailKey)) return;   // before any create
```

Three properties to carry forward:

- Scoped **per table** — the same key on the grower route is not a duplicate of a garden
  row.
- Enforced **in the Worker, not by an Airtable constraint** — a read-then-write with
  nothing behind it.
- **Not concurrency-safe.** Two simultaneous submissions of the same key could both pass
  the check. Harmless in an attended single-operator window; stated because "unique key"
  normally implies more.

## 6 · R1–R6 — refusals, zero writes

| # | Input | Reply |
|---|---|---|
| R1 | `district: 'cork'` | `400 refused · district` |
| R2 | consent sentence altered by one character | `400 refused · consent_text` |
| R3 | `over_18: 'true'` (string) | `400 refused · over_18` |
| R4 | `rent`, no permission tick | `400 refused · permission_confirmed` |
| R5 | `rent`, tick + 12-char note | `400 refused · garden_note` |
| R6 | `inherited_tenure` absent | `400 refused · inherited_tenure` |

All six exact in `state` and `field`. Counts re-read after the block: **4/1/5/5/0,
unchanged.** With the switch no longer refusing, these prove the validator.

R6 also re-confirms the preserved divergence: FROZEN G1B §5 says absent tenure is
storable-never-promoted; the Worker refuses it. Unreachable through the journey —
`decide()` only runs once every question is answered — so it is reachable only by
hand-written POST. Documented, not solved.

## 7 · Hash verification

All five `email_hash` values recomputed as SHA-256 of the lower-cased address: **5/5
exact match.** Both `consent_text_hash` values recomputed from the governed sentences:
**exact match** (garden `85c43608…`, grower `32ba8b3e…`). Consent proofs held no name,
address, district or free text — the table has seven fields and none can hold an
address.

## 8 · Surgical erasure — A2 and A6

Procedure, per subject, in order: record the row id → delete Status log rows matching
**both** `record_ref` **and** `table` → delete the subject row → stamp `erased_at` on
the Consent proofs row matched by recomputed `email_hash`.

| Artefact | Outcome |
|---|---|
| A2 Gardens row `recmuMawnaoBTIckU` | deleted |
| A6 Growers row `recQRZ1O5cNmbg4QO` | deleted |
| Their two status-log rows | deleted |
| Consent proofs 2 and 5 | **survived**, `erased_at` stamped, `email_hash` / `privacy_version` / `consent_text_hash` / `given_at` untouched |

**The three untouched subjects were proven untouched:** Gardens 3 (A1, A3, A4, all
fields intact), Status log 3 (exactly their three rows), Consent proofs 5 with only 2
and 5 stamped. Erasure was surgical, not broad.

**There is no erasure route in the Worker.** It exposes two POST paths and nothing else.
Erasure in V1 is a manual Airtable operation. G5 proves the **procedure**, not an
automated capability.

## 9 · D-G5-2 option (i) — complete cleanup

After capturing the surviving-proof evidence above, all remaining synthetic data was
removed: 3 Gardens rows, 3 status-log rows, **all five consent proofs**. Justification
stands: they are synthetic, evidence no real data subject, and a clean base before G6 is
worth more than keeping them.

**`consent_id` reached 5 and will not reset.** It is an autoNumber. The first genuine
homeowner's consent proof will be **6 or higher**. This is expected and must never be
read as a lost record. No attempt was made to reset it.

## 10 · IMPORTANT LIMITATION — the page path is NOT proven

**G5 exercised direct production Worker submissions from the permitted origin
`https://plotnua.ie`.** Real origin, real CORS check, real consent strings, real Worker,
real Airtable.

**It did NOT prove a page-driven submission through `intPayload()`.** The browser/page
submission path — the form, its payload builder, and the homeowner-visible
`intReceived()` reply — **remains unproven by this window** and must not be described as
proven. What was verified is the Worker and its data contract, not the page that will
call it.

## 11 · Scope and what this does not authorise

- **No unexpected row appeared** at any point across all three attempts. The
  `?interest=preview` exposure produced nothing.
- No code, markup or configuration changed. `prove-g3-deployed.mjs` not run.
  `INTEREST_PUBLIC` never touched. `EMAIL_ENABLED` never moved.
- **G5 completion does NOT authorise G6.** The first genuine homeowner registration
  needs separate founder authorisation.
- **G7 remains BLOCKED** pending the insurer / broker prerequisite (PS-3). Introduction
  eligibility must exclude `buying`, absent tenure and unconfirmed tenure.
