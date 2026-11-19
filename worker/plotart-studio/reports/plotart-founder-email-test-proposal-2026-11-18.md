# PlotArt payment pilot · founder-only email alerts — test proposal for approval

18 November 2026 · branch `plotart/managed-checkout-pilot` (PR #20) · **for the founder's approval**

**Outbound email stays OFF.**
- `CHECKOUT_MAIL` is not set in any deployed configuration.
- No secret has been added.
- Nothing in this proposal sends an email until you approve the recipient and the test send.

## 1. Sender, recipient and set-up

| Item | Proposal |
|---|---|
| Provider | The existing Resend integration (`src/mailer.js`), already used by PlotArt Studio's sender set-up |
| **Sender** | **PlotArt payment pilot <studio@plotnua.ie>**. This is the Studio's configured sender address, under a pilot display name. Replies go to hello@plotnua.ie. |
| **Recipient** | **One address only. Please confirm which.** It would be set as both the founder notification address and the *only* entry on the allowed-recipient list. |
| Preconditions to confirm | 1. `plotnua.ie` is verified as a sending domain in Resend. I cannot see this from here.<br>2. You add the Resend API key yourself as a secret in the `checkout-test` GitHub environment (`RESEND_API_KEY`). I never handle it. |
| What turns email on | All four together, for the sandbox test only: `CHECKOUT_MAIL=resend`, `CHECKOUT_MAIL_APPROVED=true`, the recipient on the allowed list, and a Stripe **test** key. A live key keeps everything in the test inbox. |

## 2. Samples (generated from local test data, SIMULATED)

### Urgent alert

> **Subject:** PlotArt payment pilot · URGENT · PA-O-261118-EM0001 · Amount owed to the artist is overdue
>
> OVERDUE — follow up promptly: PlotArt owes the artist EUR 6.83 on order PA-O-261118-EM0001 (processing shortfall). It was due by the end of Tuesday 17 November 2026 (Irish time). Phone the artist on the number in their seller information, pay by bank transfer, and record the payment once the bank shows it executed. Internal resolution target: Tuesday 24 November 2026 (5 working days after the deadline). The artist's deadline still applies. Founder desk: Amounts owed. Never put bank details in email.

### Daily digest

> **Subject:** PlotArt payment pilot · daily digest · Wednesday 18 November 2026 · 2 open, 0 follow-up(s) due
>
> PlotArt payment pilot · daily digest for Wednesday 18 November 2026 (Irish time)
>
> New quotes and payments are open.
>
> Open items (2):
> • PA-O-261118-EM0002: Amount owed to the artist is overdue. EUR 4.50 still owed to the artist. Due: by the end of Tuesday 17 November 2026 (Irish time) · OVERDUE.
> • PA-O-261118-EM0001: Amount owed to the artist is overdue. EUR 6.83 still owed to the artist. Due: by the end of Tuesday 17 November 2026 (Irish time) · OVERDUE.
>
> Quotes awaiting payment: 0 (0 with a Stripe page open).
>
> Founder desk: /admin/checkout. This digest never contains bank details or buyer contact details.

The digest is generated but **not scheduled**. Scheduling it, for example at 08:15 Irish time, would follow your approval.

## 3. How the test verifies the three points

### Stage 1 · local, mock Resend (done: `test/prove-founder-email.mjs`, 6/6, nothing sent)

| Check | What it proves |
|---|---|
| E1 | **Settings:** nothing is emailed unless Resend is configured, sending is approved and the key is a test key. Even then only the one allow-listed founder address is emailed. Artist and buyer messages return `held_in_test_sink`. |
| E2 | **One alert, three sweeps:** an overdue amount produces exactly **one** email to the founder, from the proposed sender with reply-to hello@plotnua.ie. The artist's overdue notice stays in the test inbox, and nothing goes to any artist or buyer address. |
| E3 | **Panel record:** the founder desk keeps the emailed alert, marked "Emailed to you: accepted by Resend (not proof that it reached your inbox)". |
| E4 | **No duplicates:** each alert has one idempotency key derived from the order, alert type, recipient and text, so a retried send of the same alert is not delivered twice. The pilot also records each reminder stage, so repeat checks never generate it again. |
| E5 | **Failed delivery (SIMULATED Resend error):** the desk shows the alert as unread with "EMAIL FAILED: … This alert was not delivered to your inbox; it is shown here only. Check the mail set-up." |
| E6 | **Digest:** generated from the desk, with no bank or buyer contact details |

### Stage 2 · one approved sandbox run (to be added once you approve)

1. **Your secrets:** you add `RESEND_API_KEY` and the confirmed recipient to the `checkout-test` environment. I send you the Actions approval link.
2. **The run creates synthetic records:**
   - one overdue amount owed;
   - one artist notice and one buyer message, each to `.invalid` addresses;
   - three automatic checks in a row.
3. **What it records:**
   - every request the Worker makes to Resend: recipient fingerprint, sender, status;
   - the founder desk delivery status for each alert.
4. **Pass criteria:**
   - exactly **two** emails reach your inbox, the urgent alert and the digest, and you confirm receipt;
   - **no** Resend request is made for any artist or buyer address; their messages are `held_in_test_sink`;
   - running the checks again sends nothing new.
5. **The failed delivery stays a simulated check.** I will not provoke a real Resend failure against your account.
6. **Afterwards:** the sandbox email settings are removed again. Live email remains a separate decision.

## 4. Changes already made on the branch (no email sent)

- **Founder alerts kept in the desk whatever the channel:** every founder alert is recorded for the panel whether it was emailed or not. Each one carries its delivery status: held in the test inbox, accepted by Resend, or failed.
- **Idempotency key** on every alert send.
- **Readable subjects,** with "URGENT" on overdue, deadline and failed-refund alerts.
- **Digest generator** (`founderDigest`), not scheduled.

## 5. Needed from you

1. **Recipient:** the single address.
2. **Sender:** confirm, or give another.
3. **Domain:** confirm that `plotnua.ie` is verified in Resend.
4. **Approval:** approve the stage 2 sandbox test send.
