# PlotArt managed checkout: consolidated status (17 November 2026, after runs 19–22)

**Test mode only.** Branch `plotart/managed-checkout-pilot` (PR #20).

Not done: merge, production deployment, production migration, issued terms, artist enrolment or live payments. The Stripe key's permissions are unchanged. Model B and all Founding Artist protections are preserved: commission-free orders, including every Founding Enquiry, stay on direct payment.

## 1. Completed work

| Area | What exists now |
|---|---|
| Fee model B | PlotArt reimburses Stripe's actual processing fee and the VAT on it, by a partial application-fee refund. Shortfalls are owed and paid directly. |
| Statements | Owed and paid amounts are separate; dispute fees appear as Stripe records them. |
| Quotes | Seller identity, address, contact and trader status, and structured returns, are required. Each issued quote is frozen as a fingerprinted snapshot. Only one open quote per work. |
| Buyer messages | The purchase confirmation, and notices for pending, failed and reversed refunds. Each message is stored once, with its fingerprint. Every delivery attempt is recorded, failures are retried (6 attempts, then flagged), and the founder can re-deliver. Buyers see the messages on their quote page. **Test sink only.** |
| Email | Reuses the project's existing Resend integration (`mailer.js`, already used by the live enquiry relay). External sending needs all of: configuration, `CHECKOUT_MAIL_APPROVED`, and in test mode an allow-list of the founder's own test inboxes. It never sends with a live key. A sink entry is recorded as "held in test sink, NOT delivered by email". A provider result is recorded as "accepted by provider", which does not prove inbox delivery. |
| Founder queue | Amounts owed, with age, due date (provisional), rule, reminders and payment evidence. Reimbursements still waiting for Stripe's fee record are listed separately. Lost-dispute commission uses the PA-GAA 9.1 30-day period. |
| Bank details | Asked for by phone and entered only in the business bank. The pilot refuses payment references that look like bank details. The drafts now say the bank keeps them as a payee (deleted when no longer needed) and in its transfer records (six years, not deletable). |
| Retention | Records are never deleted while a dispute is open; the sweep and the database both enforce this. A late dispute places a legal hold automatically. |
| Stripe access | Proposal in `STRIPE-ACCESS-PROPOSAL.md`: a separate runtime key for the public Worker with no account access. The test harness can now run the public Worker with that key (E17). |
| Drafts r8 (unissued) | PA-PAY, PA-BPT, r8 review notes with a reconciliation table, and a draft privacy-notice section. |

## 2. Evidence: real Stripe (test mode) and local mocks, kept separate

**Real Stripe runs**

| Run | Result | What it proved |
|---|---|---|
| 19 | 46 pass / 0 fail | Model B reimbursement mechanics; full-refund shortfall |
| 20 | 49 pass / 0 fail | Confirmations (E15); dispute fees €24.60 (E14); lost-dispute queue (E16); privacy access check (V1–V5); second account created (U1) |
| 21 | Onboarding link generated | Link for `acct_1Uct3vHx1OnYJa8H`, expiring 21:07 |
| 22 | 25 end-to-end pass; 1 FAIL (U3); 1 SKIP (E17b) | **E18:** after a real reversed refund, the buyer got exactly one notice ("you have NOT been repaid"), held in the test sink and shown on the quote page. All earlier end-to-end checks passed again. **U3 FAIL:** the second account is still **not onboarded** (Stripe lists every onboarding item as due), so the unfunded-refund test could not run. **E17b SKIP:** no runtime key supplied. |

**Not yet shown against real Stripe**
- the fully unfunded refund (it needs onboarding);
- the narrower runtime key (it needs the secret);
- real email delivery (deliberately off).

**Local mocked runs (latest)**

| Suite | Result |
|---|---|
| `prove-checkout-pilot` | **198/198** |
| `prove-migration-0016` | 9/9 |
| Unrelated suites (re-run in the operational-essentials round) | deploy 23/23, enquiry log 26/26, gallery order 17/17, leaving 27/27, agreement 35/35 |

The buyer-notice failure and retry paths (BN3–BN5), and the email on/off rules (MM1), are proven locally only. A real delivery failure cannot be produced against Stripe.

## 3. Remaining technical gaps

| # | Gap |
|---|---|
| T1 | ~~Fully unfunded refund not yet observed~~ **Done in run 28:** the refund succeeded immediately and the balance went to −€19.18, then −€23.26 after a further refund. Remaining: no alert for negative artist balances (optional; needs Balance Read on the Studio key). Original note: It needs the second account onboarded, then a run. The pilot's handling of pending, failed and reversed refunds is proven locally (R1–R8, BN1–BN6) and, for the reversed case, with real Stripe (E12, E18). |
| T2 | **Runtime key not yet verified.** It needs the new restricted key as a GitHub secret. If a reimbursement check fails with that key, Balance Read may also be needed. |
| T3 | **No email is sent.** The Resend set-up and your approval are needed (section 4). Until then the confirmation is reachable only through the quote link, which may not count as a durable medium: a legal-review point. |
| T4 | The Studio key still needs account reads that can expose identity details; Stripe has no narrower permission for these. Dropping the v1 account read would need a code change and sandbox check (optional). |
| T5 | Live pricing and VAT, and the countered dispute fee, are still unverified (sandbox only). |
| T6 | Professional review points from the r5–r8 notes remain: consumer law, VAT, DAC7, AML, privacy roles. |

## 4. Email: recommended option and set-up needed

**Recommendation: reuse Resend.** It is already integrated (`src/mailer.js`) and already sends live for the PlotArt enquiry relay from `plotnua.ie`, so the domain set-up exists. No new provider is needed.

Set-up, to do only when you decide to test email:
1. **Resend:** create a new API key with **Sending access only**, restricted to the domain `plotnua.ie`, named "PlotArt checkout (test)". Do not reuse the enquiry relay's key.
2. **Sender address:** choose one, for example `PlotArt <orders@plotnua.ie>`, on the already verified domain.
3. **Your test inboxes:** the addresses allowed to receive test messages, for example `colin@plotnua.ie`. Real buyers and artists must never be on this list.
4. **Your approval in writing.** I would then add, for the **test** checkout Worker only:
   - the secret `RESEND_API_KEY`;
   - `CHECKOUT_MAIL = "resend"`;
   - `CHECKOUT_MAIL_FROM`;
   - `CHECKOUT_MAIL_TEST_RECIPIENTS`;
   - `CHECKOUT_MAIL_APPROVED = "true"`.

   I would then run a test that sends only to your inboxes and report "accepted by provider" separately from what you actually receive.

## 5. Decisions for you

None of these is taken as approved. Each recommendation is mine.

| # | Decision | Recommended default | Consequence of the default | Consequence of the alternative |
|---|---|---|---|---|
| F2 | Quote only artists who sell as traders? | **Yes, traders only** (current code) | Buyers always get consumer cancellation rights. Hobby sellers can't use the pilot. | Allowing non-traders: buyers lose cancellation rights; PA-BPT 1.2 must say so on each quote. |
| F11 | Deadline to pay a shortfall | **30 days** from arising | Matches PA-GAA's 30-day refund rhythm; reminders 7 days before and when overdue. | Shorter costs more founder effort; longer weakens the "never more than commission" promise. |
| F12 | Deadline for the reimbursement | **7 days** after payment | Stripe normally records the fee within minutes; 7 days covers outages. | — |
| F15 | Who monitors the "amounts owed" queue | **The founder, weekly, plus reminders** | Low effort; overdue items are flagged. | Daily is not needed at pilot volume. |
| F14 | Narrow Stripe access | **Yes: separate runtime key A** (after the sandbox run proves it) | The internet-facing Worker can't read artist identity or bank data. | Status quo: one broad key in both Workers. |
| F9/F10 | Buyer email | **Resend, test inboxes first, then live only with separate approval** | Durable-medium confirmation becomes possible. | Without email, the confirmation is reachable only by link (a legal risk). |
| F5 | Who responds to disputes | **The artist, in their Stripe Dashboard; PlotArt supplies the evidence pack** | The artist controls the €20 countered fee. | PlotArt responding needs authority and its own time. |
| F6 | Commission after a lost dispute | **Founder action from the queue (now built), within 30 days** | Human check before money moves. | Automation is faster but riskier on edge cases. |
| F7 | Retention periods | **Keep: 6 years after settlement; 2 years if unpaid** | Matches tax and limitation periods. | Confirm with an accountant when convenient. |
| F8 | Transit insurance for every shipment | **Keep for the pilot** | Protects first sales. | Dropping it shifts risk to the artist and buyer. |
| F13 | Add-on fee exclusion list | **Keep the current list; recheck on the first live fees** | Add-on fees are shown, not reimbursed. | — |
| — | Durable medium before email | **Treat as legal-review point 2; avoid live use until email is on** | — | — |

## 6. Actions needed from you

1. **Unfunded refund:** tell me **"ready"** when you can finish onboarding straight away. I'll generate a fresh link, which expires in about 5 minutes. Run 22 found the account not yet onboarded.
2. **Optional, runtime key:** create the restricted key and add the GitHub secret, as in `STRIPE-ACCESS-PROPOSAL.md` §4. Then tell me, and I'll request the verification run.
3. **Decisions:** answer the table in section 5 as you see fit; anything you don't decide stays provisional or open.
4. **Email:** only if you want to test it now, the four set-up items in section 4.


## Addendum (22:15): run 28, fully unfunded refund. CLOSED AS PASSED

| Step | Available | Pending | Refund status (Stripe) |
|---|---|---|---|
| Before (U4) | €0.00 | €0.00 | — |
| €100 sale, €15 fee (U5) | €0.00 | €80.82 | — |
| €100 refund (U6) | €0.00 | **−€19.18** | **succeeded** at creation |
| €20 sale, €3 fee | — | — | inferred net **€15.92** (read before Stripe recorded it) |
| €20 refund (U7) | €0.00 | **−€23.26** | **succeeded** at creation |

−€19.18 + €15.92 − €20.00 = −€23.26. The €15.92 is inferred; the next run's U8 lists the actual balance transactions to confirm it.

- **What "succeeded" means.** Stripe sent the refund. It does not mean the buyer has been credited: Stripe says the credit usually appears 5–10 business days later, depending on the bank. In test mode no card is credited.
- **Who carries the negative balance.** Under `losses_collector = stripe`, Stripe's documentation says Stripe carries unrecoverable negative balances. How Stripe recovers the balance from the artist, and what the artist owes Stripe, are **marked for review** against the Stripe Connected Account Agreement. See r8 notes §4 for the sources.
- **PlotArt's Model B obligations are separate and unchanged.** PlotArt still reimburses the processing fee, returns the commission, and pays any shortfall directly.
- **Deferred:** an alert when an artist's balance goes negative.


## Addendum (23:40): runtime key, runs 29–30

- **Run 29:** a harness bug, fixed. U8 confirmed the €15.92 net: the €20 sale had €4.08 in fees (€3.00 commission plus €1.08 Stripe fee and VAT). Running net: €80.82 → −€19.18 → −€3.26 → −€23.26.
- **Run 30:** 27 pass, 1 fail.
  - The public Worker ran entirely on the runtime key (30/30 calls, no fallback, no permission errors).
  - Checkout, Model B reimbursement (€41.96, once), refunds, disputes, confirmations and buyer notices all passed.
  - Identity, bank, balance, payout, PaymentIntent and account requests were all denied (403).
  - **E17c FAIL:** creating a refund on a connected account was not denied (400 missing parameter). The key may hold a refund-write permission in connected accounts; this is for the founder to check.
  - Not exercised: Disputes Read, and session expiry from the public Worker.
- Details: `STRIPE-ACCESS-PROPOSAL.md` §5.

- **Run 31 (E17e) closes E17c.** Only the runtime key tried a valid €1.00 refund of a fresh paid charge → **403 `more_permissions_required`** ("Enabling Charges and Refunds Write ('charge_write')…"). The retry was also 403. No refund exists on the charge. **Restriction confirmed.** The run 30 400 was Stripe checking the parameters before permissions.

- **Run 32 (coverage):**
  - **E19 PASS:** natural expiry through the Worker's normal path; reservation released.
  - **E20 PASS:** dispute-fee fallback on a real dispute. The simulated input (the dispute event with its fee lines removed) is identified in the evidence, alongside Stripe's response.
  - **E17d PASS:** 7/7 calls on the runtime key.
  - The runtime-key coverage gaps are closed.

## 18 Nov 2026: runtime key adopted for the sandbox pilot; permission testing closed

- **Founder decision:** the separate restricted runtime key is adopted for the sandbox pilot. This round of permission testing is closed on runs 30–32.
- **Recorded statuses:** run 32 concluded *failure* (E17c, the no-parameters refund probe). The valid buyer-refund denial is evidenced by run 31 (E17e).
- **Live keys:** not covered; they need separate approval.
