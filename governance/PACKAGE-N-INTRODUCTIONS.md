# Package N · Commercial introductions: privacy draft, open questions, release proposal

Status: **development only**, on branch `dev/plotnua-package-n`. Nothing is merged, deployed or switched on, and no supplier has been contacted.

## 1 · What was built (all off)

| Part | Where | State |
|---|---|---|
| `/v1/introduction` route | `worker/garden-lead/src/introduction.js` | `INTRO_PUBLIC_ENABLED`, `INTRO_WRITES_ENABLED` and `INTRO_NOTIFY_ENABLED` all ship `"false"`; the `INTRO_SUPPLIERS` allow-list ships empty |
| "Request an introduction" block | `atlas-tools/plotnua_introductions.py` | switch `atlas-tools/release/plotnua-introductions.json` `public:false`; `suppliers:{}` |
| Placements | NOOK Prefab, The Pod Factory and Arctic Wellness showcases; Garden room prices; Garden saunas; Garden Retreat discovery | every page is byte-identical while the switch is off |
| Airtable table | `Introduction Requests` (schema in `worker/garden-lead/AIRTABLE-SCHEMA.md`) | **not created** |
| Founder notice | Resend, to the founder only. Carries the reference, supplier, county and timeframe; no name, email or description | needs the `RESEND_API_KEY` secret, `NOTIFY_TO` and `NOTIFY_FROM` |
| Retention | daily cron deletes expired rows (section 2A) | `INTRO_RETENTION_ENABLED` ships `"false"`; it also runs whenever writes are on |
| Deploy workflow | `.github/workflows/garden-lead-deploy.yml` | closed-only; approval in `studio-production.` |

**Two forms**
- **General form.** This is what every placement shows today. Founder wording of 26 Nov 2026, subject to data protection review: "I agree that PlotNua may use the information I provide to review my enquiry and contact me about my project. My contact details will not be shared with a supplier without my further permission."
- **Supplier-specific form.** Shown only for a supplier listed in *both* the config and the Worker allow-list, which requires a written agreement on file. It uses the approved sentence: "I agree that PlotNua may share my enquiry and contact details with [supplier name] so they can contact me about this project."

**Controls**
- The supplier sentence and the general sentence are checked by SHA-256 hash.
- Closed payload: phone, Eircode and address are refused.
- Honeypot field, and a minimum 3-second fill time.
- Rate limit of 10 per minute per isolate.
- Writes use `typecast:false`, and the Worker can only set status `RECEIVED`.
- Every record carries `delete_after` (12 months).
- While the public route is closed, every record is marked `test_record`.
- There is no automatic supplier forwarding: there is no supplier address in the code.

## 2 · Privacy notice V20: complete draft for review (NOT applied)

The live notice is V19. V20 is applied with a `privacy_v20_layer.py` and `prove-privacy-v20.py` pair, in the same way as V19, before public activation (step E). At that point `INTRO_PRIVACY_VERSION` is set to the V20 label. Wording follows the notice's existing style: Cloudflare is named as the host, and the email service is described rather than named, as in §10 today.

### New section, inserted after §6: "6A. Introduction Requests" (`id="introductions"`)

> Some PlotNua pages let you request an introduction. It is free, and you are under no obligation to buy anything.
>
> **What we collect.** We collect:
> - your name;
> - your email address;
> - your county;
> - your project timeframe;
> - if you choose to add one, a short description of your project.
>
> We also record the page you used, the date, a reference number, and the wording of the permission you gave. We do not ask for your phone number, Eircode or address.
>
> **Requests that do not name a supplier.** You agree that PlotNua may use the information you provide to review your enquiry and contact you about your project. Your contact details will not be shared with a supplier without your further permission. If we later think a particular supplier could help, we will ask you first, naming that supplier. We will share your details only if you agree.
>
> **Requests to a named supplier.** Some forms name a supplier. These appear only for suppliers that have agreed in writing to receive introductions. If you agree that PlotNua may share your enquiry and contact details with that supplier, a person at PlotNua sends them your name, email address, county, timeframe and, if you added one, your project description, so that they can contact you about your project. This is not done automatically. From that point the supplier is independent of PlotNua. It handles your details under its own privacy policy, and any conversation you have with it is between you and the supplier.
>
> **Referral fees.** PlotNua researches suppliers independently. Where a commercial referral arrangement exists, PlotNua may receive a referral fee. Such arrangements do not determine our editorial recommendations.
>
> **How it works.** Requests are received by a PlotNua service hosted on infrastructure provided by Cloudflare and recorded in Airtable. When a request arrives, an email delivery service acting for PlotNua under its data processing terms sends PlotNua a short internal notice. The notice contains the reference, county, timeframe and any supplier named. It does not include your name, email address or description.
>
> **How long we keep it.** Introduction requests are deleted automatically 12 months after they are made. We keep a request for longer only while it is still active, or where we must keep a record for legal or accounting reasons. In that case we record the reason and delete the request when the reason no longer applies.
>
> **Your choices.** You can ask us at any time to delete your request. If you gave permission for your details to be shared with a supplier, you can withdraw it at any time. Withdrawing does not affect anything already shared before you withdrew. To do either, contact hello@plotnua.ie.

### Changes to existing sections

- **§2 Information We Collect.** After the Borrowed Garden sentence, add: "If you request an introduction, we collect the information described in Section 6A."
- **§3 How We Use Your Information.** Add to the list: "to review introduction requests, reply to you and, only with your permission, introduce you to a supplier you have agreed to".
- **§10 Third-Party Services and Links.** Add after the PlotArt Founding 25 sentence: "Introduction requests described in Section 6A are received by a PlotNua service hosted on infrastructure provided by Cloudflare and recorded in Airtable, in their own table; PlotNua's internal notice of a new request is sent by an email delivery service acting for PlotNua under its data processing terms."
- **§11 Legal Basis for Processing.** Add: "For introduction requests (Section 6A): steps taken at your request, and PlotNua's legitimate interest in responding to enquiries, to review your request and reply; and your consent to share your details with a supplier you name or later agree to."
- **§12 How Long We Keep Information.** Add: "Introduction requests are deleted automatically 12 months after they are made, unless the request is still active or a record must be kept for legal or accounting reasons, as described in Section 6A."
- **§17 Changes to This Policy.** Change "Last updated" to the month V20 is published.
- **Version marker.** Use `V20 · Introduction requests, privacy notice 2026-12-INTRODUCTIONS-V1`.

## 2A · Retention: what actually happens

`delete_after` is **enforced, not just recorded**. The Worker's daily scheduled run (`purgeExpired()`, 03:23 UTC, declared in `wrangler.toml` `[triggers]`) does three things:

1. It lists rows in `Introduction Requests` matching `AND({delete_after}, IS_BEFORE({delete_after}, TODAY()), NOT({retain_reason}))`.
2. It re-checks each returned row itself, so a wrong formula cannot widen the deletion.
3. It **deletes** matching rows through the Airtable API, in batches of 10. Rows are deleted, not anonymised.

Scope and safeguards:
- It touches no other table.
- It starts as soon as `INTRO_WRITES_ENABLED` is `"true"`. `INTRO_RETENTION_ENABLED` keeps it running if writes are later switched off.
- Proved by I47–I55, and the mutation set catches dropping the re-check, ignoring `retain_reason`, oversized batches, running with the switches off, and stopping after one page.

**Residual copies outside the mechanism:**
- **Airtable's trash.** Airtable keeps deleted records restorable for a limited period, which depends on the plan. Records in the trash become unrecoverable once that period ends.
- **Airtable snapshots and revision history,** if the base uses them.
- **Supplier copies.** An email the founder forwards to a supplier is in the founder's mailbox and the supplier's. The supplier's copy falls under its own policy.
- **Notices.** The founder notice contains no personal data.

These should be stated in the ROPA entry (question 9).

## 3 · Decisions: the ten legal and data protection questions

| # | Question | Proposed resolution | Risk if wrong | Specialist advice? | Blocks public activation? |
|---|---|---|---|---|---|
| 1 | Lawful basis for general requests | Pre-contract steps plus legitimate interest; the checkbox records agreement | Low: consent is the fallback, and the wording already works as consent | Light review | Yes (the privacy text depends on it) |
| 2 | Controller roles after hand-over | Independent controllers, not joint | Medium: a joint-controller finding needs an arrangement under Art. 26 | **Yes** | No for general requests; **yes for supplier-specific** |
| 3 | Terms in each supplier agreement | A short confirmation: receiving address; use only to respond to that homeowner; GDPR handling; no marketing; any fee agreed separately | Medium: misuse by a supplier | Light review of the template | No for general; **yes per supplier** |
| 4 | Permission for a supplier named later (general requests) | Email the homeowner naming the supplier, and record the reply and date in `supplier_consent_at` | Medium: sharing without valid consent | No | No (manual process; nothing is shared until it exists) |
| 5 | Transfers (Cloudflare, Airtable, email service) | Rely on each provider's DPA, SCCs or Data Privacy Framework (DPF) certification, already used for PlotNua's registers | Low: existing processors | No (confirm the DPAs are on file) | Yes (confirmation only) |
| 6 | Retention length and the accounting exception | 12 months, deleted automatically; `retain_reason` set only where a fee is invoiced (keep a minimised record for accounting) | Low | Accountant: how long fee records must be kept | No |
| 7 | "No commercial arrangement" statements vs the referral-fee line | Keep both. They are consistent while no arrangement is active, and the existing guard forces a decision if one becomes active | Medium: misleading statement if an arrangement starts without updating the pages | No | No (guarded) |
| 8 | Is the referral-fee wording enough where a fee applies? | Generic line now; add a supplier-specific statement on that supplier's page when its fee agreement starts | Medium: consumer-law transparency | Light review | No for general; **yes per supplier with a fee** |
| 9 | Record of processing (ROPA) / short DPIA | A one-page ROPA entry before going live (purpose, data, recipients, retention, transfers, residual copies) | Low | No | **Yes** (quick to do) |
| 10 | Yard Box Phase A route | Stays off (all its switches are proved closed by the deploy guard) until Yard Box agrees in writing | High if opened without agreement | No | No (separate route, closed) |

**Before public activation of general requests:** decide questions 1 and 5, complete question 9, publish V20.
**Before each supplier-specific activation:** resolve questions 2, 3 and 8 for that supplier.

## 4 · Production release (each step needs its own founder approval)

**A. Website merge (inert) · approved in principle 26 Nov 2026.**
- Released through `atlas-tools/release/request-release.sh`; approve in website-production.
- Ships builder wiring, proofs, docs, the Worker source and the deploy workflow.
- No public page changes: proved byte-identical, and nothing is deployed to Cloudflare.

**B. Airtable table (prepared).**
- Create `Introduction Requests` in the existing PlotNua base from `worker/garden-lead/airtable-introduction-requests.json`. That file is the exact create-table API payload (22 fields; names and choices proved against the Worker by I56).
- It can be done through the Airtable connector or the Airtable interface; no new service.
- After creation, read the schema back and compare names, types and choices.

**C. Worker deploy, still closed (prepared).**
- Run `garden-lead-deploy.yml` with the merged main commit: first a dry run, then the real run. Each waits for your approval in `studio-production.`.
- The workflow:
  - refuses unless every switch ships `"false"` and the allow-list is empty;
  - reads the live settings (it handles a first deployment);
  - deploys with `--keep-vars`;
  - re-reads the settings;
  - runs `outside-check.sh` (5 checks, nothing written);
  - rolls back an existing version on failure.
- Uses the existing token `STUDIO_CF_DEPLOY_TOKEN`; no new secret.
- **Founder console actions afterwards** (secrets never pass through GitHub):
  - `AIRTABLE_BASE` variable;
  - `AIRTABLE_TOKEN` secret, scoped to this base, with create, read and delete on records;
  - `LEAD_PREVIEW_KEY` secret.

**D. Private end-to-end test (prepared).**
1. At the Cloudflare console, set:
   - `INTRO_WRITES_ENABLED=true`;
   - `INTRO_NOTIFY_ENABLED=true`;
   - `RESEND_API_KEY` (the existing key, or a new restricted key on the same account; no new service);
   - `NOTIFY_TO` (founder);
   - `NOTIFY_FROM` (the verified plotnua.ie sender).

   `INTRO_PUBLIC_ENABLED` stays `false`.
2. Run `PNL_PREVIEW_KEY=… node worker/garden-lead/test/e2e-private.mjs`. It sends ONE marked test request through the preview gate, and checks that the public route is still closed.
3. Check by hand:
   - one row with `test_record` ticked and `delete_after` 12 months ahead;
   - one founder email with no name, email or description;
   - the reference shown.
4. Prove retention: set that row's `delete_after` to yesterday, and confirm the next 03:23 UTC run deletes it.
5. Note: this step changes switches at the console. A later run of the closed-only deploy workflow refuses while they are on, which is intended.

**E. Privacy V20.** Add the layer and proof, then release, before step F.

**F. Public general requests.**
- Set `INTRO_PUBLIC_ENABLED=true` and config `"public": true`.
- Run `plotnua_introductions.py --apply`, then rebuild the three supplier showcases.
- Run the gate, then release.

**G. Supplier-specific introductions, one supplier at a time.**
- Only after that supplier's confirmation (questions 2, 3 and 8).
- Add the same slug to `INTRO_SUPPLIERS` and to the config, then rebuild, deploy and release.
- P07 refuses if the two lists differ.

**Rollback:** set `INTRO_PUBLIC_ENABLED=false` at the console (immediate), then set `"public": false` and rebuild.

## 5 · Tests on this branch

| Suite | Result |
|---|---|
| Worker: Yard Box lead behaviour / mutations | 43/43 · 18/18 caught |
| Worker: introductions, including retention and the Airtable spec / mutations | 57/57 · 19/19 caught |
| Pages: `prove-plotnua-introductions.py` | 26/26 |
| `plotnua_introductions.py --check` | OK (off, 6 placements, 0 suppliers) |
| Supplier builders `--check` | CHECK OK |
| Journey Contract | HELD |
| First lead / referral attribution | 35/35 · 8/8 |
| Deploy guard / settings reader / outside check (local) | pass / 4 cases / 5/5 |
| Image Rights Gate (all steps, locally) | see the release report |
