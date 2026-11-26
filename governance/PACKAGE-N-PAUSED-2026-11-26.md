# Package N (introductions): PAUSED by the founder, 26 Nov 2026

The founder paused Package N to return to the commercial growth objectives (analytics, search, conversion). All work is preserved. Nothing is switched on.

## Safe state at pause (verified)

| Item | State |
|---|---|
| Website | main b9330e9 (A + A2) live. Introduction block on 0 pages; `atlas-tools/release/plotnua-introductions.json` has `public: false` and `suppliers: {}` |
| Your Plot | honest Resolve wording and utm referral attribution are live (part of A) |
| garden-lead Worker | deployed closed: run 45849133802, version 510b0340. All 7 switches `"false"`. Outside check 5/5: introductions and Yard Box route both `not_open` |
| Retention cron | scheduled 03:23 UTC, inert (runs only when writes or retention are on) |
| Airtable | table "Introduction Requests" (`tblMZEdt6DrjKq4wO`, PlotNua Leads base) exists, 19 fields, **0 records**. "Garden Room Leads" untouched (1 Phase A test record) |
| Secrets | unchanged: `AIRTABLE_TOKEN`, `LEAD_PREVIEW_KEY`. No Resend key added |
| Suppliers | none contacted. NOOK's written agreement (12 Nov 2026) archived in Drive as evidence |

## Restart point: Step D (private end-to-end test)

Founder actions, one at a time:
1. Airtable token at airtable.com/create/tokens: confirm `data.records:read` and `data.records:write`, scoped to PlotNua Leads only.
2. Resend: check https://resend.com/api-keys for an unused key with sending access only, limited to plotnua.ie. Otherwise create "PlotNua introductions" with sending access, plotnua.ie only. **Do not** reuse the PlotArt enquiry relay key. Also confirm the account holder.
3. Cloudflare → plotnua-garden-lead → Variables and Secrets:
   - `INTRO_WRITES_ENABLED`, `INTRO_NOTIFY_ENABLED` and `INTRO_RETENTION_ENABLED` set to `true`;
   - `NOTIFY_TO` = `colin@plotnua.ie`;
   - `NOTIFY_FROM` = a plotnua.ie sender;
   - secret `RESEND_API_KEY`.

   Leave `INTRO_PUBLIC_ENABLED` at `false`. Also confirm the account holder.
4. Run `worker/garden-lead/test/e2e-private.mjs` with the preview key, in the founder's own environment. The key is never pasted into chat. Then complete the manual checks D14–D18.
5. Close the test configuration again: writes and notify back to `false`; retention stays `true`.

## After Step D (each needs separate founder approval)
- Approve the final Q1, Q9 and Privacy V20 (Drive document 11).
- Publish V20.
- Step F: general public activation.
- Step G, NOOK: a small deploy-workflow change to allow the config's supplier list, then add `nook-prefab` with agreement reference "written agreement 12 Nov 2026"; introductions go to dimple@nookprefab.com.

## Documents
- `governance/PACKAGE-N-INTRODUCTIONS.md`
- Drive folder "Package N — commercial introductions", documents 01–11, plus the archived DPAs and the NOOK evidence record.
