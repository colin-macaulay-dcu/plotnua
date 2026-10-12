# G6 PREPARATION · THE GARDEN OWNER REGISTER — READY FOR CONTROLLED ACTIVATION

**Date:** 12 October 2026
**Status:** PREPARED · NOT OPEN. `INTEREST_PUBLIC = false` · `WRITES_ENABLED = "false"` · `EMAIL_ENABLED = "false"` · not pushed · not deployed
**Authority:** founder decisions of 12 October 2026 on the audit `DISC-025-GARDEN-OWNER-INTEREST-AUDIT-2026-10-12.md`
**Related:** [`PRIVACY-VERSION-2026-10-PHASE2-V3.md`](PRIVACY-VERSION-2026-10-PHASE2-V3.md) · [`DISC-025-V2-POST-FREEZE-AMENDMENT-2-2026-10-12.md`](DISC-025-V2-POST-FREEZE-AMENDMENT-2-2026-10-12.md) · [`G3-TO-G6-DECISION-BRIEF.md`](G3-TO-G6-DECISION-BRIEF.md)

---

## 1 · Decisions applied

| | decision | applied as |
|---|---|---|
| D1 | Route A — the existing G3 panel, Worker and Airtable register | no second register, no new service, Worker source untouched |
| D2 | option (ii) — tenure only | `intPayload()` trimmed; notice → V3; `PRIVACY_VERSION` → V3 in `wrangler.toml` |
| D3 | approved wording; four pilot areas; elsewhere welcome without implying matching; bounded amendment to frozen V2 | offer, CTA and out-of-pilot confirmation re-worded inside the G3 regions only |
| D4 | page-only honeypot | hidden `website` field; filled → nothing sent, truthful not-saved state |
| D5 | prepare for controlled activation; founder reviews; weekly procedure; research target of five | §5 and §6 below |

## 2 · Files changed

| file | change |
|---|---|
| `disc025-borrowed-garden-check.html` | G3 regions only (see Amendment 2) |
| `privacy.html` | Section 7 added; Airtable and Cloudflare; retention; renumbered 8–17; Oct 2026 |
| `worker/garden-register/wrangler.toml` | `PRIVACY_VERSION` V3 (deploy-time only) |
| `atlas-tools/build-g6-owner-register.py` | **new** bounded builder |
| `atlas-tools/prove-g6-owner-register.py` | **new** privacy guards + capability proofs for the guards and the builder |
| `worker/garden-register/test/prove-g3.mjs` | G11d/G11e/G23f3 re-pointed to D2; G15d re-anchored (it had become vacuous); G15e to D3; G11f, G23f4, G23h1–6, G23i, G23j, G30–G30f added |
| `worker/garden-register/test/prove-g3-mutations.mjs` | M15/M19 inverted (their anchors were removed by D2); M31–M39 added; `MUT_SLICE` option |
| `worker/garden-register/test/prove-tenure-invariance.mjs` | accounts for exactly the four D2 keys, with non-vacuity checks T5k/T5l |
| `atlas-tools/prove-landmarks.mjs` | L10 re-stamped to the amended `<main>` |
| `atlas-tools/prove-journey-exit-mutations.py` | inputs pinned to Job 1 commit `9a7c136` (E0e made the control fail on any later authorised page edit) |

## 3 · Tests executed

| suite | result |
|---|---|
| `prove-g3.mjs` (page guards, jsdom) | **196 / 196** (was 179) |
| `prove-g3-mutations.mjs` | **36 / 36 caught**, 0 blind, vacuous or crashed (run in four `MUT_SLICE` shards) |
| `prove-tenure-invariance.mjs` | **12 / 12**; capability-checked: a drifted `source` and a re-added answer are both caught |
| `prove-guards.mjs` (Worker) | 74 / 74 (unchanged) |
| `prove-worker-mutations.mjs` | 3 / 3 caught (unchanged) |
| `prove-g6-owner-register.py` | **43 / 43** — 16 privacy guards, 12 privacy capability cases, 14 builder refusals + control |
| `prove-first-lead.mjs` (privacy assertions) | 35 / 35 |
| `prove-landmarks.mjs` | 140 / 140 |
| `prove-landmarks-capability.py` | 18 caught / 0 blind |
| `prove-journey-exit-mutations.py` | 19 caught / 0 blind — identical to HEAD |
| `prove-g1b-tenure-builder-guards.py` | 15 capable — identical to HEAD |
| `prove-*.mjs` suite | **35 / 38**, identical to the pre-change baseline |
| Wellness journey / applicability | 143 / 143 · 52 / 52 |
| Image rights | manifest up to date · GATE PASS 40 publishable · provenance 11 / 11 |
| Scratch hygiene capability | 5 / 5 |
| Handover byte anchors (8) | all unchanged |

**Own defects caught during this work, recorded plainly:**
- PV15 matched the existing "can be guaranteed to be completely secure" disclaimer, a negation; narrowed to affirmative forms.
- PV11 came back BLIND — the email address alone also appears elsewhere — and was strengthened to own the deletion instruction.
- Builder case C2 duplicated only part of its anchor; fixed.
- C9 was first written as a no-op; replaced with a real engine edit.
- The draft privacy text added an un-consented purpose ("to understand where garden space might be available") and overclaimed "the version of the notice you were shown". Both were corrected, and PV16 now guards the first.

**Not run, and why:**
- `prove-deployed*.mjs` — these call the live Worker; they belong to the activation sequence.
- `prove-g3-review-harness.mjs` — a founder-review aid that needs a generated harness directory.
- `prove-g3-builder-guards.py` — replays the original G3 builder over a page that already contains G3. It shows the same 3 false positives at untouched HEAD; pre-existing.

**Environmental, not regressions:**
- `prove-supplier-publication-gate.mjs` and `-capability.mjs` write to a hard-coded `/tmp/pg11-no-exception.json` that an earlier session left owned by another user in this VM.
- `prove-disc026-discovery.mjs` is the known pre-existing failure.

## 4 · Open items for founder review — none of these are resolved here

| # | item | why it matters |
|---|---|---|
| R1 | **Execute Airtable's DPA** (airtable.com/dpaform) | Airtable states its DPA is not binding until executed. Privacy Section 7 describes its transfer terms, so it should not go live first. This also covers the supplier-enquiry records already held in Airtable |
| R2 | **Confirm Airtable base collaborators** on `appUie3wPmPITfMW7` are you alone | Section 7 says the record is private to PlotNua. Not verified in this work |
| R3 | **The Worker still accepts the four dropped keys** | page-level minimisation only. Optional Worker change: ignore them, then re-prove |
| R4 | **Retention is manual** | you own it. Set the first review date (§6 step 7) |
| R5 | **Tenure is sent for every tenure** | required by the deployed Worker; recorded as the reading of D2 |
| R6 | **Confirmation wording for out-of-area** | the founder-approved V2 line "If somebody nearby is looking, we will email you and ask first" now sits beside "we are not looking for anybody to introduce outside those areas". Not contradictory, but you may want to read them together |
| R7 | **Honeypot residual** | a person whose browser filled the hidden field would see the truthful "didn't go through" message. Retrying won't help them; `hello@plotnua.ie` is offered |
| R8 | **Pushing `main` ships everything ahead of `origin/main`** | that's the 12 earlier Garden Retreat / proof commits as well as this one. Decide that together |
| R9 | **Legal review** | the wording describes, it does not assure. A short review of Section 7 by someone qualified in Irish data protection would be prudent before opening |
| R10 | **What counts as "genuine"** and whether the five must be in the four pilot areas | §6 proposes a definition; your call |

## 5 · Exact activation sequence

Each step is yours. **Stop** if any check fails. Steps 1–6 can happen with nothing open to the public.

1. **Approve this package** (visual acceptance of Amendment 2 and the privacy text).
2. **Resolve R1 and R2.** Execute the Airtable DPA and confirm the collaborators.
3. **Confirm zero.** Read Gardens, Growers, Status log, Consent proofs and the fifth table — all 0.
4. **Push** `main` (see R8). GitHub Pages publishes `privacy.html` V3 and the amended page. The register remains removed from the DOM for every visitor.
5. **Deploy the Worker, still closed:** from `worker/garden-register/`, `npx wrangler secret list` (expect `AIRTABLE_TOKEN`, `AIRTABLE_BASE`), then `npx wrangler deploy`. This carries `PRIVACY_VERSION` V3 with writes off. Run `node test/prove-deployed.mjs`, `prove-deployed-switch.mjs` and `prove-g3-deployed.mjs`; expect `not_open`.
6. **V3 controlled dry run (G5 pattern, your records only).**
   - Set `WRITES_ENABLED = "true"` and deploy.
   - From `…/disc025-borrowed-garden-check.html?interest=preview`, submit one `own` and one `rent` record.
   - In Airtable, confirm **no** `inherited_spare_corner`, `inherited_way_in`, `inherited_your_own_use` or `inherited_result_key`; confirm `privacy_version = 2026-10-PHASE2-V3` and a Consent proofs row holding a hash only.
   - Erase both by the PRIVACY-V2 §7 procedure; confirm the consent proofs survive.
   - Return the tables to zero.
   - Set `WRITES_ENABLED = "false"` and deploy.
7. **Open — one founder-authorised release, in this order:**
   - (a) `WRITES_ENABLED = "true"`, deploy, and verify one more time with a preview submission plus erasure.
   - (b) A bounded builder flips `INTEREST_PUBLIC = true` in its own commit, and the page is pushed.

   Writes go first so that no homeowner ever meets "The register isn't open yet".
8. **Smoke test from the public URL** (no `?interest=preview`). Submit one record of your own, confirm it in Airtable, erase it.
9. **Begin the weekly review** (§6).

**Emergency close.** Set `INTEREST_PUBLIC = false` and push; set `WRITES_ENABLED = "false"` and deploy. Either alone stops new records; do both.

## 6 · Proposed weekly review procedure (founder, ~20 minutes, same day each week)

1. **Open Gardens.** Filter `submitted_at` within the last 7 days. Note the count.
2. **Screen each record.** A record counts as **genuine** if it has a plausible first name and email, a chosen area, and is not one of your own test records.
   - Obvious junk (nonsense, links in the note, throwaway domains): erase by the §7 procedure and note "1 junk removed".
3. **Renters.** Confirm `permission_confirmed = true` and a note of at least 20 characters. The Worker enforces this; you are checking it, not re-deciding it.
4. **Over-sharing in the note.** If someone typed an address, Eircode, phone number or health detail, delete that text from `garden_note`. Note that you did, without copying it.
5. **Do not change `status`.** Do not stamp `human_review_by` / `human_review_at`; those fields are reserved for promotion under G7, which stays blocked. Do not contact registrants except to answer their own emails.
6. **Leaving requests.** Check `hello@plotnua.ie` for any. Erase within the week (the outer limit for responding is one month). Reply to confirm.
7. **Retention.** Erase any record whose `submitted_at` is more than 24 months old (first possible: October 2028). Record the date you checked.
8. **Log the week** in a short private table with no personal data: date, new records, genuine (in-pilot / elsewhere), junk removed, leaving requests, notes edited.
9. **Target check.** The research target is **five genuine garden-owner expressions of interest**. Proposed review point: when five genuine records exist, or eight weeks after opening, whichever comes first, decide whether to continue, widen or close (R10). This is a count, not a promise to anyone on the register.

---

## ADDENDUM · 12 October 2026, later the same day (append-only)

- **R3 CLOSED IN SOURCE.** See [`G6-R3-WORKER-DEPRECATED-FIELDS-2026-10-12.md`](G6-R3-WORKER-DEPRECATED-FIELDS-2026-10-12.md). The Worker now refuses any garden submission carrying one of the four deprecated keys. It is not yet deployed.
- **R1:** the founder reports the Airtable DPA signed on 12 October 2026.
- **Activation step 6** is now mandatory, because the Worker source changed. Add to it: one direct request to the deployed Worker carrying `inherited_result_key` → expect `400 refused`, field `inherited_result_key`, and nothing in Airtable.
