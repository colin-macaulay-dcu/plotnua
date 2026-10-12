# G6 · R3 CLOSED — THE WORKER REFUSES DEPRECATED PROPERTY CHECK FIELDS

**Date:** 12 October 2026
**Status:** CLOSED IN SOURCE · committed locally · **NOT DEPLOYED** — the live Worker is still `66ee90e2…` and still accepts these fields until the next deploy
**Authority:** founder instruction "G6 final data-minimisation safeguard", 12 October 2026
**Closes:** R3 of [`G6-PREPARATION-GARDEN-OWNER-REGISTER-2026-10-12.md`](G6-PREPARATION-GARDEN-OWNER-REGISTER-2026-10-12.md)

## 1 · The defect, measured before the fix

The new suite was run against the unfixed Worker first. **Every one of the 40 deprecated-field assertions failed.** Each such request was answered `200 received` and made **4 Airtable calls**: the address check, the Gardens create carrying the field, the status log and the consent proof. R3 was real, not theoretical.

## 2 · How the fields are rejected

`worker/garden-register/src/index.js`, applied by `atlas-tools/build-g6-worker-deprecated-fields.py`:

| layer | what it does |
|---|---|
| **1 · explicit refusal** | `DEPRECATED_GARDEN_KEYS` lists `inherited_spare_corner`, `inherited_way_in`, `inherited_your_own_use`, `inherited_result_key`. A garden submission that **contains** any of them — by key presence, whatever the value, including `""` and `null` — is answered `400 { ok:false, state:'refused', field:<key> }`. |
| ordering | The refusal runs **first**: before field validation, before the tenure and renter rules, before consent hashing, **before the write switch** and before any Airtable call. With writes off it is still a `400` naming the key, never a `503 not_open` that would hide the reason. |
| **2 · no write path** | The four keys are no longer parsed or written. If layer 1 were ever deleted, they still could not be stored. Guarded on the source by D8, since no request can observe it while layer 1 is in place. |

**Unchanged:**
- **Validation:** required `inherited_tenure`; the G1B §5 renter rule (tick plus a statement of at least 20 characters); consent hashing against the approved sentence; `over_18`.
- **Writing:** the `interest_submitted` ceiling; `typecast:false`; `privacy_version` read from the environment (V3 in `wrangler.toml`).
- **Request handling:** origin and fetch-metadata checks; the rate limit; the no-oracle reply shapes; the grower route.
- **Storage and deletion:** the Airtable schema, the erasure procedure, and the hash-only consent proof.

The page sends none of the four keys (D2), so homeowners see no change.

| | sha256 |
|---|---|
| Worker source before (G5-certified, currently deployed) | `66ee90e2d94968ee59a1f2c71674956735b1f593c1d4ef7a97b77f477e177c79` |
| Worker source after | `17bdc4672387aff9394876ec8f479a6f4e03a77144bdf0e671fe485b2d519d7a` |
| `wrangler.toml` | unchanged by this work · `WRITES_ENABLED="false"` · `EMAIL_ENABLED="false"` · `PRIVACY_VERSION="2026-10-PHASE2-V3"` |

## 3 · Tests

| suite | result |
|---|---|
| **`test/prove-g6-deprecated-fields.mjs`** (new) | **72 / 72** after the fix · 28 / 68 before it (all 40 deprecated-field assertions failing) |
| **`test/prove-g6-worker-mutations.mjs`** (new) | **10 / 10 caught**, 0 blind / vacuous / partial |
| **`atlas-tools/prove-g6-worker-builder.py`** (new) | **10 / 10**: control applies; 9 refusals proven |
| `test/prove-guards.mjs` | 74 / 74 (unchanged) |
| `test/prove-worker-mutations.mjs` (M27, M29, M30) | 3 / 3 caught (unchanged, preserved as it was) |
| `test/prove-tenure-invariance.mjs` | 12 / 12 |
| `test/prove-g3.mjs` (page) | 196 / 196 |
| `atlas-tools/prove-g6-owner-register.py` | 43 / 43 |

The new suite drives the **real Worker with the write switch ON** against a stub Airtable that records every call and never reaches the network. With writes on, a request that is not refused *would* write, so "zero Airtable calls" is measured rather than a by-product of the switch.

| requirement | proven by |
|---|---|
| 1 legitimate registrations still work | D1, D1b: `own`, `rent` with permission and `buying` are each received, with exactly one Gardens record |
| 2 tenure preserved | D2, D2b: stored exactly as sent; renter permission and statement stored |
| 3 renter safeguards | D3: no tick, no statement, absent tenure and unknown tenure are each refused with zero calls |
| 4 deprecated fields rejected | D4, D4b–D4g: each key with a valid value, an empty string, null and junk; for renters; all four together; with writes off; ahead of ordinary validation; a look-alike key is not over-matched; the list is exactly these four |
| 5 no Airtable record | D5: zero Airtable calls for every refused request |
| 6 consent enforced | D6, D6b: altered sentence, grower sentence, empty sentence and `over_18:false` are each refused with zero calls |
| 7 status and privacy intact | D7a–h: status ceiling; no deprecated key in any write; privacy V3 from the environment; consent proof of exactly four fields, hash only; `typecast:false` on every create; status log moving only to `interest_submitted`; foreign origin 403; switch off → `not_open` |

**Own defects caught on the way, recorded plainly:**
- Three mutation anchors were VACUOUS on the first run: the write-switch and privacy-version lines occur in both routes, and the permission count was wrong. The harness refused to score them; they are now scoped to the garden handler.
- The builder's ordering gate used `index()`, which would have crashed rather than refused.
- The builder's capability proof found it **BLIND** to a rewrite that set a promotable status directly (B8). A status-ceiling gate was added, the case re-run as CAPABLE, and the builder confirmed to reproduce the applied source byte for byte.

## 4 · Remaining blockers

| # | item | state |
|---|---|---|
| — | **The deployed Worker still accepts the four fields** | until the next `wrangler deploy` from `worker/garden-register/`. Activation step 5 deploys it. |
| — | **New controlled dry run** | the source no longer matches the G5-certified `66ee90e2…`, so step 6 of the activation sequence is now required, not optional. It must also send one direct request carrying `inherited_result_key` to the *deployed* Worker, and confirm `400 refused` with nothing in Airtable. |
| R1 | Airtable DPA | **founder reports it signed 12 October 2026**. Not independently verifiable from here. |
| R2 | Airtable base collaborators | **open**, not verified |
| R8 | pushing `main` ships 14 commits | **open** |
| R9 | legal review of privacy Section 7 | **open**, recommended |
| R10 | definition of "genuine" for the target of five | **open** |
| new | `check_saved_at` | still accepted as an optional field (not on the founder's list). The page never sends it. It is a timestamp, not a Property Check answer. Founder may wish to deprecate it the same way. |
| new | the four Airtable columns still exist in Gardens | schema preserved as instructed. Nothing can now be written to them. Hiding or deleting them later is a schema decision, not a code one. |
