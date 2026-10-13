# ART SPACE REGISTER · DISC-024 OPEN YOUR HOME TO ART · CONTROLLED BUILD

**Date:** 13 October 2026
**Status:** BUILT AND TESTED LOCALLY · **CLOSED** (`INTEREST_PUBLIC = false`) · Worker **not deployed** (`WRITES_ENABLED = "false"`, `EMAIL_ENABLED = "false"`) · no Airtable base, record or token created · privacy notice **not changed** · not pushed.
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
| `discovery-open-your-home-to-art.html` | One contextual cross-link to Buy Original Irish Art, plus a scoped `.pn-xlink` style. |
| `discovery-a-home-for-art.html` | One contextual cross-link to Open Your Home to Art, plus the same style. |
| `atlas-tools/build-art-space-register.py` | **new** · bounded builder, guards R1–R13 |
| `atlas-tools/build-art-cross-links.py` | **new** · bounded builder, guards X1–X4 |
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
