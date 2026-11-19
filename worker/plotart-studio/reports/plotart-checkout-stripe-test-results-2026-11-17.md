# PlotArt managed checkout pilot: Stripe test-mode results

17 November 2026 · branch `plotart/managed-checkout-pilot` · Stripe sandbox, test mode only · nothing merged or deployed · live payments off.

Final run: **16**, [Actions run 44131079901](https://github.com/colin-macaulay-dcu/plotnua/actions/runs/44131079901). Result: **34 passed, 0 failed, 1 skipped, 3 measurements recorded**.

Test connected account: `acct_1UclJXHx1Olx8cdw`. It was created through Accounts v2 and onboarded by Colin with test data.

## 1. Results from the Stripe test API (run 16)

### Account and configuration

| Check | Result |
|---|---|
| P1: create the account | SKIP. The run reused the account created in run 3, where P1 passed. |
| P1c, P1d, P3: account configuration | PASS. Confirmed by Stripe: the artist pays the fees, Stripe carries losses and collects the requirements, and the artist has the full Dashboard. Card payments are active. |
| P1e: onboarding complete | PASS. Details submitted, charges and payouts enabled, and nothing due. |
| P2: onboarding link | PASS (Account Links v2). |

### Checkout Sessions

| Check | Result |
|---|---|
| P4, P4b, P5 | PASS. €1,075 in EUR on the artist's account, with Adaptive Pricing off. A repeated request returns the same session, and the session can be expired. |

### Payments and fees

| Check | Result |
|---|---|
| P6, P6b: payment with commission | PASS. A €1,075 direct charge with a €150 application fee. Stripe creates the fee record asynchronously; it appeared within about 3 seconds. |
| P7, P7b: actual fees | Measured (section 3). |

### Refunds

| Check | Result |
|---|---|
| P8, P8b, P9: full refund and commission refund | PASS. The buyer refund does not return the commission automatically. PlotArt's own refund of the €150 commission is processed only once, even if the request is repeated. |
| P10: partial refunds | PASS. €75 of commission returned in total. |
| P11: refund larger than the available balance | Measured (section 4). |
| P11b | PASS. |
| P12: refund that fails after first succeeding | PASS. Status changed to failed (`expired_or_canceled_card`) about 2 minutes later. |

### Disputes

| Check | Result |
|---|---|
| P13, P14: disputes lost and won | PASS. Each took €50 plus a €24.60 fee from the artist; one closed lost, the other won. |

### End to end: hosted Checkout in a real browser, with genuine Stripe-signed webhooks forwarded by the Stripe CLI

| Check | Result |
|---|---|
| E1: account shown as ready | PASS |
| E2: buyer sent to Stripe's hosted Checkout | PASS |
| E3a: payment on the hosted page | PASS. Stripe returned the buyer to the pilot with `result=success`. |
| E3: payment marks the order paid | PASS. `evt_1UcpoSHx1Olx8cdwYsojNJEX` (`checkout.session.completed`) marked the order paid and the work sold. |
| E3c: event matched to the right order | PASS. The order's own session, the matching PaymentIntent, and no other order touched. |
| E4: charge matches the ledger | PASS. €1,075 charged; €150 commission; €75 delivery outside commission. |
| E5: partial refund through the pilot | PASS. €100 refunded and €15 of commission returned. |
| E6: abandoned checkout | PASS. A real `checkout.session.expired` released the reservation. |
| E7a: payment with the dispute test card | PASS |
| E7: dispute recorded | PASS. The order is disputed and the dispute open. |
| E7c: dispute matched to the right order | PASS. `evt_1UcpokHx1Olx8cdw9xF2PAwm` is on the disputed PaymentIntent, and no other order was touched. |
| E8: expected events all processed | PASS. All expected events arrived and were processed, and none failed. |

In run 16, the dispute event again arrived **before** the payment completion. The pilot answered it with HTTP 500 and parked it. It then replayed it when the completion arrived. The Stripe CLI delivery log shows this order of events.

## 2. Local results (simulated Stripe, not provider evidence)

| Suite | Result |
|---|---|
| Checkout pilot | 137/137 |
| Deployment tooling | 23/23 |
| Enquiry log | 26/26 |
| Gallery order | 17/17 |
| L1, L2: live key refused, test key present | PASS |

## 3. Fees: balance-transaction breakdown on a €1,075 sale (sandbox)

| Line | US test card (P7) | Irish test card (P7b) |
|---|---|---|
| Stripe processing fee | €34.11 | €16.38 |
| VAT on Stripe's fee (`tax`) | €7.85 | €3.77 |
| PlotArt application fee | €150.00 | €150.00 |
| **Net to artist** | **€883.04** | **€904.85** |

**Sandbox observations compared with what is verified:**

- **Irish card.** The sandbox charged €16.38, which equals 1.5% + €0.25. That matches Stripe's published rate for standard EEA cards. Premium EEA cards (1.9% + €0.25) were not tested.
- **US card.** The sandbox charged €34.11, which works out to 3.15% + €0.25. Stripe's published rate for international cards is 3.25% + €0.25, which would be €35.19. The sandbox is therefore not a reliable source for live pricing on non-EEA cards.
- **VAT on fees for Irish accounts.** Stripe's support page states that for Stripe account holders in Ireland, VAT applies to all Stripe fees at the prevailing standard rate. The VAT is added on top of the fees and invoiced monthly. The sandbox applied 23%.
- **VAT on fees for other European accounts.** Stripe supplies these accounts from Ireland without charging VAT on its fees. The account holder may have to self-assess under the reverse charge. The pilot accepts IE and GB artists, so their fee lines will differ.
- **Whether VAT is a real cost to the artist.** This depends on the artist's own VAT position. Stripe does not state it, and it must not be assumed.

**Proposed change to the PA-PAY and PA-BPT examples (awaiting Colin's approval):**

- Show Stripe's fee before VAT.
- Add a separate line: "VAT on Stripe's fee, if any: depends on the artist's Stripe account country and VAT status".
- Use the Irish 23% figure only as an illustration.
- Give no single "net to artist" figure that has VAT built in.

## 4. Financial risks found

1. **Refunds are not held when the available balance is short.** In the P11 runs, Stripe paid refunds larger than the available balance straight away, drawing on incoming funds. In run 14 this took the pending balance negative (−€73.83). A refund larger than available plus incoming funds together has not been tested; it needs an emptied balance and payout permission.
2. **Disputes cost the artist €24.60, win or lose.** That is €20 plus 23% VAT for an Irish account (the VAT applies as in section 3). The artist also bears the disputed amount until the dispute is decided.
3. **A refund can fail minutes after first succeeding.** The pilot records this as "buyer not repaid; the seller repays directly".
4. **Fees for non-EEA cards are much higher.** Draft examples should not imply that every sale is charged 1.5% + €0.25.

## 5. Defects found and fixed during testing

**Pilot code:**

- Account creation moved to Accounts v2, because Stripe refuses v1 account creation for new platforms. Account Links v2 no longer takes the `configurations` field.
- `payment_method_types` was replaced with `allowed_payment_method_types` (endive API). API versions are now pinned.
- Adaptive Pricing is turned off. Before this, buyers outside the euro area were shown converted US$ prices.
- Events that arrive before their payment completion are now replayed by the pilot itself, using the current object fetched from Stripe. The sweep also replays them as a backstop. Before this, the pilot relied only on Stripe redelivering the event.

**Test harness:**

- It now waits for the asynchronously created application fee and balance transaction.
- It clicks the main Pay button, not "Pay securely with Link".
- It serves the pilot's return page in the test browser.
- It records browser diagnostics, with inputs masked and values redacted.
- E3 and E7 are marked as blocked, not failed, when no payment was made.
- E8 passes only when the expected events arrived.
- P1, P1c, P1d and P2 are reported separately.

## 6. Not yet verified

- Live pricing and VAT on a live Irish account.
- Premium-card and UK-card fees.
- A refund larger than the available and incoming balance together.
- A dispute closed through the pilot's own handling of `charge.dispute.closed` with real signed events. Only `charge.dispute.created` was delivered end to end.
- Behaviour when live Stripe redelivers webhooks.

## What to send to ChatGPT

The PlotArt managed-checkout pilot passed Stripe test mode end to end in run 16: 34 passed, 0 failed, 1 deliberate skip (account creation reused from run 3).

- **Verified against the real Stripe test API:**
  - Accounts v2 configuration: the artist pays fees, Stripe carries losses, and the artist has the full Dashboard.
  - Checkout in euro with Adaptive Pricing off.
  - A €1,075 payment with a €150 application fee.
  - Full and partial refunds, and commission refunds that are processed only once.
  - A refund that fails asynchronously.
  - Disputes, both won and lost.
- **End-to-end checks, with real hosted-Checkout payments in a browser and genuine Stripe-signed webhooks:**
  - The completion event marked the correct order paid. This was cross-checked against Stripe's session and PaymentIntent.
  - A partial refund was processed through the pilot.
  - An abandoned checkout released the reservation.
  - A dispute that arrived before its payment completion was replayed by the pilot and applied to the correct order. This replay logic was added after run 15 exposed a reliance on Stripe redelivery.
- **Fees (sandbox):**
  - Irish card: €16.38 processing fee plus €3.77 VAT, which matches Stripe's published 1.5% + €0.25.
  - US card: €34.11 plus €7.85 VAT; Stripe's published international rate is 3.25% + €0.25.
  - Stripe's support pages confirm that VAT is added to Stripe fees for Irish accounts. Other European accounts are not charged VAT by Stripe but may self-assess. Whether VAT is a real cost depends on each artist's VAT status.
- **Draft examples:** the proposal is to show the fee before VAT, with VAT as a conditional separate line. This awaits approval.
- **Risks:** refunds can take the artist's balance negative; disputes cost €24.60 (€20 + VAT) whether won or lost; refunds can fail later; non-EEA cards cost much more.
- **Status:** nothing merged or deployed; production unchanged; live payments off.
