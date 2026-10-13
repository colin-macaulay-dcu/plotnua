# ART SPACE REGISTER · DISC-024 OPEN YOUR HOME TO ART · CONTROLLED BUILD

**Date:** 13 October 2026
**Status:** BUILT AND TESTED · **CLOSED** (`INTEREST_PUBLIC = false`) · Worker **not deployed** (`WRITES_ENABLED = "false"`, `EMAIL_ENABLED = "false"`) · no Airtable base, record or token created · privacy notice **not changed** (V4 builder ready, unpublished). See **§11, Activation preparation**, which supersedes §7–§9 where they differ.

> **Since this build (13 Oct 2026):**
> - The two art Discoveries merged into **A Home for Art** (`discovery-a-home-for-art.html`). Open Your Home to Art is its primary branch (`#open-your-home-to-art`). The old Discovery URL is a redirect.
> - The DISC-024 Property Check (`disc024-open-your-home-to-art.html`) and its saved-result identity (`disc024-open-your-home-to-art`) are **unchanged**, and the register still lives on that check.
> - The two cross-links and `atlas-tools/build-art-cross-links.py` were **retired** with the merge (see `governance/A-HOME-FOR-ART-MERGE-2026-10-13.md`).
**Authority:** founder decision of 13 October 2026, "Art Space Register · controlled build".

## 1 · What it is, and what it is not

| | |
|---|---|
| **It is** | A private register of homeowners' **expressions of interest** in offering space for artists' finished work: Store, Display, Open (visitors by arrangement) and Help sell. |
| **It is not** | Matching, introductions, bookings, payments, automatic email, a public listing, or a promise of income. There is no artist route, table or record of any kind. |
| **Scope** | The existing DISC-024 opportunity only. No studios, residencies or general creative activity. Builder guard R8 refuses that wording. |
| **Separation** | Its own Airtable base, its own Cloudflare Worker, its own token and its own privacy section. It shares nothing with the Garden Owner Register. |
| **Introductions** | Not authorised. They need evidence of genuine artist demand first (founder decision, 13 Oct 2026). Homeowner interest is tested independently of that. |

## 2 · Files

| file | change |
|---|---|
| `disc024-open-your-home-to-art.html` | **Four bounded insertions only (449 lines added, 0 removed):** scoped CSS; the register section after the My Plot save band; one call at the end of `reveal()`, passing only `space`, `level` and `money`; the register script. Questions, outcomes, engine, save keys, journey exit: byte-identical. |
| `discovery-open-your-home-to-art.html` | *(retired 13 Oct 2026)* One cross-link. The page is now a redirect to A Home for Art. |
| `discovery-a-home-for-art.html` | *(retired 13 Oct 2026)* One cross-link. The page is now the merged Discovery. |
| `atlas-tools/build-art-space-register.py` | **new** · bounded builder, guards R1–R13 |
| `atlas-tools/build-art-cross-links.py` | *(retired and deleted 13 Oct 2026 with the merge)* |
| `atlas-tools/prove-art-space-register.py` | **new** · guard-capability proof, 27 breaks |
| `worker/art-space-register/src/index.js` | **new** · the Worker |
| `worker/art-space-register/wrangler.toml` | **new** · both switches `"false"`; no base id and no secret |
| `worker/art-space-register/package.json` | **new** |
| `worker/art-space-register/test/prove-art-worker.mjs` | **new** · 64 Worker guards, network stubbed |
| `governance/PRIVACY-VERSION-2026-10-PHASE2-V4-DRAFT.md` | **new** · privacy section draft; **not published** |
| this file | **new** |

**Not touched:** `privacy.html`, `disc025-borrowed-garden-check.html`, `worker/garden-register/**`, the Garden base, Search, Results, Atlas, My Plot (`your-plot.html`) and every other page. R13 asserts the Garden and privacy files are unchanged.

## 3 · Homeowner flow

1. The homeowner completes the DISC-024 Property Check. Any of the seven results qualifies.
2. Below the result and the My Plot save band, the invitation appears **only** in private preview (`?interest=preview`). In production, the section is **removed from the DOM**.
3. The **invitation** is the founder-approved text, verbatim (pinned by SHA-256, guard R7). CTA: "Register my interest".
4. **Form:**
   - **Required:** first name, email, county (26 counties), "Which would you consider?" (tick at least one of four).
   - **Optional:** kind of space, whether money is part of it ("It isn't an offer."), a note with a warning not to include an address, Eircode, phone number or valuables.
   - Kind of space, the four options and money are **pre-filled** from the check's answers and can all be changed.
   - **Honeypot**, then the **single consent tick** carrying the founder-approved sentence.
   - A collapsible "what we keep, and what we never ask for" notice.
5. **States:**
   - **received:** "You're on the register" — not a matching service, no artist will contact you, how to leave.
   - **not_open:** "The register isn't open yet". This is what any submission gets today.
   - **unavailable:** truthful failure, also shown when the honeypot is filled.
   - **refused:** names the field; nothing saved.

## 4 · Consent and privacy

- **Consent sentence:** *"I'm over 18 and agree that PlotNua may keep my registration details and contact me about the Open Your Home to Art pilot. I understand I can withdraw my consent at any time."*
  - It exists once on the page, written with `textContent` and sent verbatim.
  - The Worker hashes what arrives and compares it with its own constant. Whitespace normalises; a change of meaning is refused (`consent_text`).
  - Guard R3 keeps page, Worker and approved text identical.
- **Consent proof** (separate table): email fingerprint (SHA-256), notice version, consent-text hash, time. Never the address.
- **Privacy notice:** the Section 8 draft is in `PRIVACY-VERSION-2026-10-PHASE2-V4-DRAFT.md`. It is **not published**, and R2 refuses to open the register until `privacy.html` carries `id="art-space-register"`.
- **Retention:** 24 months, recorded as a **policy to review before opening**.

## 5 · Security and minimisation

| control | where |
|---|---|
| Ships closed; removed from the DOM unless public or preview | page (R2) |
| Worker writes off · no email adapter · no GET handler · single route | Worker (W1–W10, S1–S7) |
| Four hard stops: writes switch, token, base, canonical consent | Worker |
| **Strict keys:** any key outside the 10 allowed keys (address, Eircode, phone, surname, tenure, Property Check result, honeypot…) is refused **before** the write switch | Worker (K × 9) |
| Strict vocabularies: 26 counties, four options (1–4, unique), space, money; `typecast:false` | Worker (F) + page (R4) |
| Status ceiling: only `interest_submitted`; introductions impossible from code | Worker (P4, S2) |
| A repeat address gets the same "received" with no write, so the reply can't reveal who is registered | Worker (D1) |
| Origin locked to `https://plotnua.ie`; fetch-metadata checks; no credentials; 4 KB body cap; in-memory rate limit | Worker (W4–W6, B1, RL1) |
| No surname, address, Eircode, town, phone, photo, tenure or value field; no file or tel input | page (R6, R10) |
| Only three check answers pre-fill the form; nothing else from the check is read | page (R11) |
| No My Plot, localStorage, analytics or garden endpoint in the register script | page (R12) |
| No promise wording: guarantee, earn, income, booking, matched, commission | page (R7) |

## 6 · Tests (13 Oct 2026)

| suite | result |
|---|---|
| `worker/art-space-register/test/prove-art-worker.mjs` | **64 / 64** |
| `build-art-space-register.py --check` (R1–R13) | PASS |
| `build-art-cross-links.py --check` (X1–X4) | PASS |
| `prove-art-space-register.py` | **27 / 27 breaks caught**; controls pass; files byte-identical |
| Browser (Playwright, desktop 1440 and mobile 390) | **51 / 51**: closed state absent from the DOM at load and after a result, with no request; preview flow; pre-fill; validation with focus and `aria-invalid`; exact payload keys; confirmation; not_open; honeypot; Not now; cross-links navigate |
| axe-core WCAG 2.1 A/AA on the register (invitation, form, error) | **0 violations** (the preview badge colour was darkened to pass) |
| `prove-landmarks.mjs` | 140 / 140 |
| `prove-g6-owner-register.py` (Garden privacy guards) | 43 / 43 |
| `worker/garden-register/test/prove-guards.mjs` | 74 / 74 (unchanged) |
| `prove-journey-exit-mutations.py` | 19 caught, 0 blind |
| `build-search-index.py --check` · `prove-discovery-library-capability.py` · `build-provider-explorer.py --check` · disclosure firewall | all pass |

## 7 · Airtable setup — FOUNDER ONLY (do not do until approved)

> **Superseded by §11.2.** The canonical schema is now `worker/art-space-register/airtable-schema.json`, checked against the Worker by guard R14. It adds two formula fields and the views. The list below is kept for history.

1. In the same Airtable account (its DPA is signed), create a **new base** named **"PlotNua Art Space Register"**. Collaborators: you only. Share-to-web: off.
2. Create table **Hosts**, with fields named exactly:
   - `first_name` — Single line text (primary field)
   - `email` — Email
   - `email_key` — Single line text
   - `county` — Single select. Options exactly: `carlow, cavan, clare, cork, donegal, dublin, galway, kerry, kildare, kilkenny, laois, leitrim, limerick, longford, louth, mayo, meath, monaghan, offaly, roscommon, sligo, tipperary, waterford, westmeath, wexford, wicklow`
   - `ways` — Multiple select: `store, display, open, help_sell`
   - `space` — Single select: `a_wall, a_room, dry_store, not_sure`
   - `money` — Single select: `no_money, fee_for_space, share_if_sells, not_decided`
   - `host_note` — Long text
   - `over_18` — Checkbox
   - `status` — Single select: `interest_submitted` (the only option)
   - `submitted_at` — Date, with time, GMT
   - `privacy_version` — Single line text
   - `consent_text_hash` — Single line text
   - `source` — Single select: `property_check`
   - `human_review_by` — Single line text (reserved, leave blank)
   - `human_review_at` — Date with time (reserved, leave blank)
3. Create table **Status log**: `record_ref` (Single line text, primary) · `from_status` · `to_status` · `actor` · `reason` (Single line text) · `at` (Date with time, GMT).
4. Create table **Consent proofs**: `email_hash` (Single line text, primary) · `privacy_version` · `consent_text_hash` (Single line text) · `given_at` · `withdrawn_at` · `deletion_honoured_at` (Date with time, GMT; the last two filled by hand).
5. Delete Airtable's default sample rows and fields. Confirm all three tables show **0 records**.
6. Create a **personal access token** named `plotnua-art-space-register-worker`:
   - scopes **`data.records:read` and `data.records:write` only** (read is needed for the duplicate-address check);
   - access: **this base only**;
   - **do not reuse** the Garden token, and never paste a token into chat or the repository.
7. Note the new base id (`app…`) for the deploy step.

## 8 · Cloudflare setup — FOUNDER ONLY

> **Superseded by §11.3.** `AIRTABLE_BASE` is now a **persistent secret**, not a deploy-time `--var`. With `--var`, the next plain `wrangler deploy` would drop it.

Run from `04 Deploy/plotnua-g6-release/worker/art-space-register/`:

1. `npx wrangler whoami` — confirm the same account as the Garden Worker.
2. Deploy **closed**: `npx wrangler deploy --var AIRTABLE_BASE:<new base id>`. `wrangler.toml` keeps `WRITES_ENABLED = "false"`.
3. `npx wrangler secret put AIRTABLE_TOKEN` — paste the art token at the prompt.
4. `npx wrangler secret list` — expect `AIRTABLE_TOKEN` only.
5. Confirm the endpoint matches the page: `https://plotnua-art-space-register.colin-a41.workers.dev/v1/art-space-register/host`. If your workers.dev subdomain differs, the page's `ENDPOINT` must be changed through the builder.
6. Closed probe: a POST from `?interest=preview` returns **"The register isn't open yet"**, and Airtable stays at 0.

**Stop here.** Everything after this point needs your explicit approval.

## 9 · Remaining steps before opening (each needs founder approval)

1. Approve the remaining homeowner-facing wording: form labels, the on-page notice, confirmation, not-open and failure states. The heading, invitation, CTA and consent are already approved.
2. Review the retention policy; legal review of the Section 8 draft; publish privacy notice V4 (a bounded builder) and decide the Garden Worker's version label.
3. Create the base and token (§7); deploy closed (§8).
4. **Dry run:**
   - set `WRITES_ENABLED = "true"` and deploy;
   - submit two records of your own from `?interest=preview`;
   - in Airtable, confirm the fields above only, `privacy_version = 2026-10-PHASE2-V4`, a consent-proof row holding a hash only, and a status-log row;
   - send one direct request with an `eircode` key and expect `400 refused`, `unexpected_field`, with nothing stored;
   - erase both records (the consent proofs remain);
   - set writes back to `"false"` and deploy.
5. **Open, writes first:**
   - enable writes and deploy;
   - then a founder-authorised builder change sets `INTEREST_PUBLIC = true`. R2 allows it only once the privacy section is live;
   - push.
6. Smoke-test from the public URL with your own record, then erase it.
7. **Weekly review**, as for the Garden Owner Register:
   - count new records;
   - remove junk;
   - strip any address, Eircode or phone number from notes;
   - process leaving requests within the week (one month at most);
   - erase at 24 months;
   - log the totals with no personal data;
   - never set `human_review_*`;
   - contact registrants only to answer them, or about the pilot within the consented purpose.
8. **Review trigger:** **10 genuine homeowner registrations or 8 weeks after opening**, whichever comes first. **A review only.** It does not authorise matching or introductions.

**Emergency close:** set `INTEREST_PUBLIC` back to false through the builder and push; set `WRITES_ENABLED = "false"` and deploy. Either one alone stops new records; do both.

## 10 · Notes

- **No analytics events.** The register adds none. The existing anonymous funnel events are unchanged. If you want "register opened" or "submitted" counts, that's a separate decision.
- **The artist side** (a future validation process) is not part of this build and needs its own consent, table and privacy text before any artist data is stored.

## 11 · Activation preparation (founder direction, 13 Oct 2026, 21:09)

**The register remains CLOSED.** Nothing external was created:
- no base, token, record or deploy;
- no privacy publication;
- no change to the Garden Owner Register's Worker, consent, base, page or privacy version (it stays **V3**).

### 11.1 · Founder decisions recorded

| # | Decision |
|---|---|
| 1 | **Wording.** The invitation, consent sentence and four participation categories are retained. A commitment statement is added: *"Registering your interest doesn't commit you to hosting artwork, inviting visitors into your home or entering into any arrangement. PlotNua is simply exploring whether homeowners might be interested in these possibilities."* It is pinned by SHA-256 (guard R7b). |
| 2 | **Retention (provisional until privacy and legal review).** Homeowner registrations: 24 months. Minimal deletion records: 12 months after the deletion is completed. |
| 3 | **Garden Owner Register.** Stays on privacy version V3. Untouched. |
| 4 | **Spam.** Existing protections retained. No Turnstile. |
| 5 | **Airtable.** Schema prepared. The base and token are **not** created. |
| 6 | **Privacy.** A bounded V4 builder is implemented. **Unpublished** until founder approval and legal review. |
| 7 | **Worker.** `AIRTABLE_BASE` is a persistent secret. **Not deployed.** |
| 8 | **Opening guard.** Activation is possible only once the privacy and Worker-version conditions hold. **Not activated.** |

### 11.2 · Airtable

The canonical, machine-checked specification is `worker/art-space-register/airtable-schema.json`. It covers:
- three tables: Hosts, Status log, Consent proofs;
- field types and option lists;
- two formula fields: `erase_after` (24 months) and `remove_after` (12 months after `deletion_honoured_at`);
- views;
- token scopes and access rules.

There are **no linked-record relationships, by design**, so the minimal proof survives a deletion. Guard R14 refuses if the file lacks a field the Worker writes or if its options differ from the Worker's vocabularies.

### 11.3 · Cloudflare (founder, when approved)

Run from `04 Deploy/plotnua-g6-release/worker/art-space-register/`:
1. `npx wrangler whoami` — confirm it is the same account as the Garden Worker.
2. `npx wrangler deploy` — this deploys **closed**, because `wrangler.toml` keeps writes off.
3. `npx wrangler secret put AIRTABLE_BASE` — paste the new base id.
4. `npx wrangler secret put AIRTABLE_TOKEN` — paste the art-only token at the prompt. Never paste it into chat.
5. `npx wrangler secret list` — expect exactly `AIRTABLE_BASE` and `AIRTABLE_TOKEN`.
6. **Closed probe.** A POST from `?interest=preview` returns "The register isn't open yet", and Airtable stays at 0 records.

**Strict-key probe:** a request carrying `eircode` returns `400`, `refused`, `unexpected_field`, and nothing is stored.

**Dry run (founder-approved, and only after privacy V4 is live):**
1. `npx wrangler deploy --var WRITES_ENABLED:true`.
2. Submit two of your own records from `?interest=preview`.
3. Check the fields, the consent proof and the status log in Airtable.
4. Erase both records.
5. `npx wrangler deploy` to switch writes back off.

Keep the dry run short: `?interest=preview` works on the live page, so while writes are on it records real submissions.

**Rollback, fastest first:**
1. Revoke the Airtable token.
2. `npx wrangler deploy` (writes off).
3. `npx wrangler rollback`.
4. Close the page through the builder and push.
5. `npx wrangler delete`.

### 11.4 · Privacy V4

- **Builder:** `atlas-tools/build-privacy-v4.py`.
  - `--check` builds V4 in memory from the live V3 page. Guards:
    - V1: the text matches the draft word for word;
    - V2: numbering 1–18, and Section 7 is pinned and unchanged;
    - V3: required statements are present;
    - V4: consistency with the Worker, the on-page notice and both Workers' version labels;
    - V5: no invented assurances;
    - V6: only the five declared changes.
  - `--preview PATH` writes outside the repository only.
  - `--apply` is refused until `APPROVAL` records the founder's approval, the legal review and the "Last updated" label.
- **Five declared changes:**
  1. a new Section 8;
  2. Sections 8–17 renumbered to 9–18;
  3. one third-party sentence;
  4. one retention line;
  5. the "Last updated" label.
- **Publication co-edits.** `atlas-tools/prove-g6-owner-register.py` gets three bounded edits:
  - the section count, 1–17 becomes 1–18;
  - one heading used as a mutation anchor follows the renumbering;
  - mutation anchors are taken inside Section 7 when they occur there, because Section 8 repeats six of Section 7's legal sentences.

  On a V3 page these are behaviour-identical. Nothing else of the Garden register changes.
- **Rehearsal.** `atlas-tools/prove-privacy-v4.py` rehearses publication in a throwaway clone. It checks that the Garden privacy proof (43/43), the Garden open-gate proof (14/14), landmarks (133), first-lead (35) and the closed register (R1–R14) all pass on V4, and that the Garden Worker and check page are untouched.

### 11.5 · Opening guard (R2), as of this change

`INTEREST_PUBLIC` may be `true` only when **all** of these hold:
- (a) `privacy.html` carries exactly the governed V4 Section 8;
- (b) the Art Worker's `PRIVACY_VERSION` equals that version;
- (c) `OPEN_APPROVAL` records the founder's approval to open, the legal review and the dry run.

R13 now allows `privacy.html` to differ from git HEAD only by exactly the V4 builder's output. The merge builder's M8 now ignores only the register's four marked blocks on the DISC-024 check, which this builder governs.

### 11.6 · Remaining steps to open, in order

1. **Founder:** review the final wording (form labels, on-page notice, end states, commitment statement).
2. **Legal review:** Section 8 and both retention periods. Also confirm the 12-month deletion-note period for **24-month erasures**, not only for withdrawals.
3. **Founder:** set `APPROVAL` in the V4 builder (as a committed change), run `--apply`, and push. This publishes privacy V4.
4. **Founder:** create the base exactly as in `airtable-schema.json` (or approve Claude creating the empty base through the connector), then create the token yourself.
5. **Founder:** follow §11.3 steps 1–6, plus the strict-key probe.
6. **Founder:** the dry run (§11.3).
7. **Founder:** set `OPEN_APPROVAL`, set `INTEREST_PUBLIC = True`, run `--apply`, deploy with writes on, and push.
8. **Smoke test:** one public record of your own, then erase it. The weekly review starts.

The review trigger is unchanged: **10 genuine registrations or 8 weeks**. It is a review only and does not authorise matching.
