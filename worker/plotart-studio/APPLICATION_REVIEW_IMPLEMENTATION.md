# PlotArt Gallery Artist application review — implementation plan (draft, not deployed)

## Verified current architecture (16 November 2026)
- Studio: `worker/plotart-studio/src/index.js`, `src/assets.js` (ADMIN_HTML).
- Founder-only authenticated application GET endpoints read private EU R2 `APPLICATIONS`; no application decision POST endpoint exists.
- Gallery Artist applications are in Airtable table `Gallery Artist applications` (separate from Founding 25).
- Existing fields: `status`, `review_notes`, `decision_reason`, `decided_at`, `status_changed_at`, `decision_emailed_at`, `studio_invited_at`.
- Existing deployed Airtable automations for Gallery Artist applications only handle new-record alerts and applicant acknowledgements. They are triggered on record creation, not status edits.
- Studio mailer defaults to `MAILER=none`; it must not be assumed that Studio can send applicant email.
- Existing invitation remains separate from application acceptance and artist agreement.

## Proposed smallest safe implementation
1. **Secure data path first**: decide on a scoped, secret Airtable token or a dedicated authenticated application-decision Worker endpoint. Never expose tokens, base IDs or applicant email addresses to the public page. Verify Cloudflare Access founder role on each request.
2. **Read**: GET founder-only application decision state from Airtable by the R2-stored record ID and application reference. Validate both; fail closed on mismatch.
3. **Write**: POST decision endpoint accepts `accept`, `request_information`, or `decline` with bounded review notes and message. Re-read current state, enforce allowed transitions, idempotency and optimistic concurrency, then update the correct Airtable record. Keep Founding 25 out of scope.
4. **Request Information**: require a non-empty applicant-facing message; store it in a purpose-built field or append to an auditable correspondence log, not in the private `decision_reason`. Do not mark an email sent until the delivery provider confirms success.
5. **Email**: reuse existing authorised Gmail/Airtable sender after inspecting its exact deployed configuration. Prefer an explicit outbox record with unique action ID, pending/sent/failed states, and one-at-a-time delivery to prevent duplicates. Never rely on a status-only trigger to send an unreviewed message.
6. **Accept**: update status and decision timestamp; do not create an account, invite, send a message, or publish automatically. Keep the existing separate Studio invitation workflow.
7. **Decline**: record internal reason separately from the applicant-facing message. Require confirmation before delivery.
8. **UI**: add three actions to the existing founder-only application view, plus review notes, current status, delivery state and an explicit confirmation screen. Preserve existing private image review and deletion functions.
9. **Tests**: unit-test role restrictions, missing/invalid references, state transitions, concurrent clicks, duplicate deliveries, provider failure, safe rendering/escaping, and no changes to Founding 25. Use fake Airtable and email providers in tests; do not email real applicants.
10. **Release gate**: review branch diff, test results, deployed bindings and email automation statuses before founder-approved merge and deployment.

## Current status
Investigation only. This file is a design checkpoint on a non-production branch; no applicant data, statuses, automations, secrets or live pages were modified.
