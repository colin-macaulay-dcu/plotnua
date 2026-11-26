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

**Two forms**
- **General form.** This is what every placement shows today. The homeowner gives PlotNua permission to review the request and reply. Nothing goes to a supplier without the homeowner's separate, later permission.
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

## 2 · Privacy notice amendment: draft V20 (NOT applied)

Apply through a `privacy_v20_layer.py` / `prove-privacy-v20.py` pair, as V19 was, at the same time as activation. Set `INTRO_PRIVACY_VERSION` to the version label.

**New §6A "Introduction requests"** (anchor `id="introductions"`)

> Some PlotNua pages let you request an introduction. It is free and you are under no obligation.
>
> **What we collect:**
> - your name;
> - your email address;
> - your county;
> - your project timeframe;
> - optionally, a short description of your project.
>
> We also record the page you used, the date, a reference number and the wording of the permission you gave. We do not ask for your phone number, Eircode or address.
>
> **General requests.** If you ask for an introduction without a named supplier, you allow PlotNua to use your details to review your request and reply to you. We will not share your details with any supplier unless you later give us separate permission for that named supplier.
>
> **Requests to a named supplier.** If the form names a supplier and you tick the box agreeing that we may share your enquiry and contact details with them, a person at PlotNua sends your name, email address, county, timeframe and description to that supplier so they can contact you about the project. It is not sent automatically. Named-supplier forms appear only for suppliers that have agreed in writing to receive introductions. From then on, the supplier handles your details as an independent controller under its own privacy policy.
>
> **Referral fees.** Where a commercial referral arrangement exists, PlotNua may receive a referral fee. Such arrangements do not determine our editorial recommendations.
>
> **Who processes your details:**
> - Cloudflare, which hosts our introduction service;
> - Airtable, which holds our records of requests;
> - Resend, which sends PlotNua an internal notice that a request has arrived. The notice does not contain your name, email or description.
>
> These providers may process data outside the EEA under appropriate safeguards, such as standard contractual clauses.
>
> **Legal basis:**
> - your consent, for sharing your details with a named supplier;
> - steps taken at your request, and our legitimate interest in replying, for reviewing and answering your request.
>
> You can withdraw consent at any time. Withdrawal does not affect anything already shared.
>
> **How long we keep it:** up to 12 months from your request, unless the request is still active or a longer period is required for legal or accounting reasons.

**Consequential edits**
- **§2 Information We Collect:** add "introduction requests".
- **§10 Third-Party Services:** add Resend if it is not already listed. It is listed for PlotArt; confirm the wording covers PlotNua.
- **§11 Legal Basis:** cross-reference §6A.
- **§12 Retention:** add "Introduction requests are kept for up to 12 months, as described in Section 6A."
- **§17 Changes:** add the V20 entry.

## 3 · Unresolved legal and data protection questions (founder / adviser)

1. **Lawful basis for general requests.** The draft uses pre-contract steps plus legitimate interest; consent is the alternative. The UI checkbox is framed as agreement either way. Confirm the choice.
2. **Controller roles.** The draft treats PlotNua and each supplier as independent controllers after a hand-over, not as joint controllers. This needs confirmation, and a short data-sharing clause in each supplier agreement.
3. **Supplier agreement terms.** Before any supplier is added to the allow-list, the written agreement should cover:
   - the receiving address;
   - use limited to responding to that homeowner;
   - GDPR handling;
   - no onward marketing;
   - a response expectation;
   - any referral fee, as a separate commercial term.
4. **Separate consent for a later-named supplier** (general requests). Decide the method, for example an email reply quoting the exact sentence, recorded in `supplier_consent_at`. Also decide who records it.
5. **Transfers.** Confirm SCC/DPF coverage in the Airtable and Resend DPAs for this purpose, and that both are listed as processors.
6. **Retention.** Is 12 months right for unsuccessful requests? What legal or accounting basis justifies keeping a record linked to a paid referral fee (for example 6 years for accounting)? Should a minimised record be kept in that case?
7. **Disclosure placement and the existing "no commercial arrangement" statements.**
   - `garden-room-prices-ireland.html` says "PlotNua has no commercial arrangement with any of them", guarded by `check-commercial-disclosure.py`.
   - The supplier pages say "there is no paid placement".
   - The new conditional referral-fee line is consistent with both today. If NOOK's affiliate programme or TimberIN's code becomes an active arrangement covering a listed maker, the guard will require the founder to change one statement or the other.
8. **Consumer-law/CCPC transparency.** Confirm that the referral-fee wording is sufficient where a fee actually applies, or whether that supplier's page needs its own specific statement.
9. **DPIA-lite.** The processing is low-volume and low-risk, but a short record of processing (ROPA) entry is advisable before going live.
10. **Yard Box Phase A.** Yard Box sits in the separate Phase A lead Worker (switched off) without a written agreement to receive enquiries. It must not be switched on until it has one.

## 4 · Production release proposal (each step needs its own founder approval)

**A. Website (inert)**
- Merge this branch through the normal release route: `atlas-tools/release/request-release.sh introductions-n1 --no-wait`, then approval in website-production.
- Because the switch is off, no page changes. Only builder wiring, proofs and docs ship.

**B. Airtable**
- Create the `Introduction Requests` table exactly as in the schema, in the existing base. No new paid service is needed.

**C. Worker deploy (still closed)**
- The garden-lead Worker has no deploy workflow today. Proposed: add `garden-lead-deploy.yml`, modelled on `studio-deploy.yml`, with:
  - a dry run;
  - a `garden-lead-production` approval environment;
  - a check that the commit is on main;
  - a live-settings comparison.
- Alternatively, a one-off manual `wrangler deploy`.
- With every `INTRO_*` switch false, the deploy changes nothing visible. Verify with the preview key: the route answers `not_open` without the key, and writes nothing while writes are off.

**D. Private end-to-end test**
- Set `INTRO_WRITES_ENABLED=true`, add the `RESEND_API_KEY` secret, set `NOTIFY_TO` (founder) and `NOTIFY_FROM` (a verified plotnua.ie sender) and `INTRO_NOTIFY_ENABLED=true`. The public route stays off.
- Submit one request with the preview key, then confirm:
  - one `test_record` row exists with the correct `delete_after`;
  - one founder email arrives, with no personal data in it;
  - the reply carries the reference.
- Delete the test row.

**E. Privacy V20**
- Apply the layer and proof, then release, **before** step F.

**F. Public activation of general requests**
- Set `INTRO_PUBLIC_ENABLED=true` (Worker) and `"public": true` (config).
- Run `python3 atlas-tools/plotnua_introductions.py --apply` for the guide and discovery fenced regions, and rebuild the three supplier showcases.
- Run the gate, then release.

**G. Supplier-specific introductions, one supplier at a time**
- Only after that supplier's written agreement (section 3, question 3) is on file:
  - add the same slug to `INTRO_SUPPLIERS` and to config `suppliers`, with the agreement reference;
  - rebuild;
  - deploy the Worker and release the site.
- `prove-plotnua-introductions.py` P07 fails if the two lists differ.

**Rollback:** set `INTRO_PUBLIC_ENABLED=false` (immediate, no site release needed), then set `"public": false` and rebuild.

## 5 · Tests on this branch

| Suite | Result |
|---|---|
| Worker: Yard Box lead behaviour / mutations | 43/43 · 18/18 caught |
| Worker: introductions behaviour / mutations | 46/46 · 14/14 caught |
| Pages: `prove-plotnua-introductions.py` | 26/26 |
| `plotnua_introductions.py --check` | OK (off, 6 placements, 0 suppliers) |
| Supplier builders `--check` (NOOK, Pod Factory, Arctic Wellness) | CHECK OK |
| Journey Contract (93 checks) | HELD |
| First lead / referral attribution | 35/35 · 8/8 |
| Image Rights Gate (all 32 steps, locally) | 32/32 |
| Browser payload checked against the real Worker handler | 200 received |
