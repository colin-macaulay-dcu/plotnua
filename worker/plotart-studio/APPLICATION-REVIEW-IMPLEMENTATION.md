# PlotArt Gallery Artist application decisions — implementation contract

Status: investigation complete for existing read paths and Airtable automations; no production changes.

## Verified existing architecture
- Studio Worker: worker/plotart-studio/src/index.js. Founder-only application list/detail API reads private APPLICATIONS R2 JSON; no decision-writing API.
- UI: worker/plotart-studio/src/assets.js, ADMIN_JS appView(ref), currently directs founder to Airtable.
- Live Airtable base appS4gWOxuZqJyWvU, table tblEQ8CiXFWMlWqsE, 'Gallery Artist applications'. Includes status, review_notes, decision_reason, decided_at, decision_emailed_at, studio_invited_at.
- Two deployed automations on this table: new-application alert (recordCreated), acknowledgement (recordCreated; Gmail sends then sets acknowledged_at). Neither triggers on record updates, so neither sends decision emails.
- Studio has separate Gallery Artist invitation process; application acceptance must never create/publish an account automatically.
- F25 workflow is separate; preserve unchanged.

## Safe incremental implementation
1. Add read-only founder-only Airtable application status lookup by application reference and exact R2 stored record id; never trust client-provided Airtable IDs. Fail closed if token/base/table bindings absent. Use existing scoped secret only after verifying Cloudflare bindings.
2. Render status, notes and decision controls only for PA-AP applications. Leave F25 unchanged.
3. Add founder-only authenticated POST decision endpoint with same-origin/X-Studio protections, strict body limits and validation, status transition rules, and idempotency. On acceptance: record status/reason/time only; Studio invite stays separate. On information request: require nonempty message; on decline: require reason. Keep internal decision_reason distinct from external message.
4. Establish a single approved outbound-email path. Do not send via Studio mailer until its live provider is verified. Prefer existing Airtable Gmail integration if a secure send-once queue with message content and send timestamps can be implemented. Confirm emails explicitly in UI; mark sent only after successful send. Prevent duplicate sends on retries and protect against partial failure.
5. Audit all changes (actor, reference, before/after, timestamps, send result) without duplicating sensitive applicant data. Preserve retention and consent proof.
6. Test status changes, missing credentials, invalid references, F25 isolation, replay/duplicate email, email failure/retry, invite isolation, and Access authorization. Never use a real applicant for testing.
7. Deploy only after founder approval and a verified dry run.

## Blockers before live implementation
- Verify production Cloudflare Worker secret bindings and whether the existing scoped Airtable token is available to Studio (do not expose secret).
- Choose and validate a reliable send-once decision-email mechanism with existing Gmail automation; the current recordCreated automations do not cover decisions.
- Ensure a secure per-request audit and idempotency strategy.
