# PlotArt payment pilot · “Pause new quotes and payments” (founder pause for absences)

18 November 2026 · branch `plotart/managed-checkout-pilot` (PR #20) · sandbox only · **for the founder's review**

Built as Option 1.

**Recorded (founder, 11:05):**
- **Run 36** is the sandbox verification of “Pause new quotes and payments”: a session opened before the pause and paid during it, and a buyer link refused during the pause.
- **The expiry and resume checks** (PZ5 and PZ7) are **local simulations**.

**Wording revised (11:05):**
- **Founder checklist:** shows one payment status per quote, either “The buyer can still pay on the Stripe page already opened until ‹session expiry›.” or “The buyer cannot start payment while paused.”, with the original quote expiry in both cases.
- **Buyer note:** now reads “Payments are temporarily paused. If payments resume before your quote expires, you can pay using this link.” The expiry stays visible at the top of the page, and the contact address appears once, in the footer.
- **Expired quotes:** keep their existing message. Founder email, production deployment and access for a cover person remain separate decisions. Nothing is merged or deployed.

---

## 1. What it does

| While paused, the server refuses | Who sees what |
|---|---|
| Creating a new managed-checkout order | Founder: "New quotes and payments are paused (founder absence). Resume them on the checkout desk first." |
| Issuing a quote | Founder: same message |
| Opening a Stripe Checkout Session from an unpaid quote, including through an existing buyer link | Buyer: the quote is shown without the pay button, with this note: "Payments are temporarily paused. If payments resume before your quote expires, you can pay using this link." No Stripe session or reservation is made. |

**Not changed:**
- the quote's expiry date;
- everything else: signed Stripe events, automatic reimbursements, the 15-minute checks, alerts, refunds, commission returns, reconciliation, bank-transfer records and corrections. Every deadline keeps running.

**Founder control** (top of `/admin/checkout`; founder only):
- **To pause:** "Pause new quotes and payments", with a required return date and an optional note.
- **While paused:** shows **PAUSED**, since when, and the expected return date, with a "Resume new quotes and payments" button.
- **History:** each pause and resume is recorded and kept.
- **Note beside the control:**

  > While paused, PlotArt refuses new managed-checkout orders, issuing quotes, and starting payment from an unpaid quote, including existing buyer links. A Stripe payment page that a buyer already has open may still complete (for up to about 30 minutes) and is recorded as normal. Existing deadlines continue: reimbursements, amounts owed to artists, refunds and disputes stay due on their dates. Quote expiry dates do not change.

**Absence checklist** (under the control; open while paused). It covers anything due before your return date plus two working days, and lists:
- **open Stripe payment pages** and when each expires;
- **quotes awaiting payment** and their expiry;
- **every item due in that window**, with the manual action it needs before you leave: "Pay before you leave", "Follow up before you leave", "set a follow-up", or "arrange agreed cover". This covers processing reimbursements, amounts owed, lost-dispute commission, refunds waiting at Stripe, and flagged orders.

Screenshots (local test data, simulated):
- `reports/pause-control-paused-2026-11-18.png`
- `reports/buyer-quote-paused-2026-11-18.png`

## 2. Real Stripe sandbox — run 36

Run [44289573853](https://github.com/colin-macaulay-dcu/plotnua/actions/runs/44289573853): approved, job 10:59:27–11:00:27 UTC, **conclusion: success**.

| Check | Result | What happened |
|---|---|---|
| **E23** session opened before the pause, paid during it | **PASS** | 1. Checkout Session `cs_test_a0UM…` opened, valid until 11:31:10.<br>2. Pause switched on at 11:00:10.<br>3. The buyer paid €200 on the real hosted page at 11:00:19.<br>4. The signed `checkout.session.completed` was processed **once**; the charge was booked **once** (€200.00).<br>5. The reimbursement went ahead: €8.06, `fr_1Ud6bDHx1Olx8cdwX2Tzq5yc`, accepted 11:00:23.<br>The pause stayed on throughout. |
| **E23a** another buyer link during the pause | **PASS** | HTTP 409 with the paused note. **No** session was created at Stripe, and the quote's expiry was unchanged. The absence checklist listed the open session and its 11:31 expiry. |
| E17b–d | **PASS** | The runtime key still has five permissions and made all 9 calls. |

**What the buyer saw after paying during the pause:** Stripe returned them to the pilot's return page:

> Thank you. Your payment for quote ‹ref› has been confirmed. ‹Artist› and PlotArt will be in touch about delivery.

**What the founder saw:** the order paid, the reimbursement made, and the control still showing **PAUSED**.

## 3. Local tests (mock Stripe; expiry times SIMULATED)

242/242 checks pass; migration 9/9 (24 pilot tables); deployment tooling 23/23.

| Check | Result |
|---|---|
| PZ1 | Only the founder can pause. A return date is required and cannot be in the past. The control's label and note are as above. |
| PZ2 | The absence checklist lists both open sessions, the quote awaiting payment, and the items due before the return date (plus two working days), each with its action |
| PZ3 | New order refused (409); issuing refused (409). The buyer link shows the paused note and no pay button, and paying is refused. No session, no reservation; expiry unchanged. |
| PZ4 | A session opened before the pause and paid during it is recorded once, even with repeated and duplicate events. Sold once; reimbursement made once. |
| PZ5 | **Session expires during the pause:** the reservation is released and the quote returns to payable-later. The buyer sees the paused note; expiry unchanged. |
| PZ6 | **Still works while paused:** a founder refund to a buyer; a commission return after a lost dispute; reconciling an interrupted checkout; recording a bank transfer and its return (one correction notice); automatic reimbursements; the sweep; the alerts panel |
| PZ7 | **Quote expires before resuming:** the buyer sees "This quote has expired. Please contact hello@plotnua.ie." and it stays expired after resuming. After resuming, quotes can be issued and an unexpired quote can be paid. Pause history is kept. |

## 4. Still to note

- **An open Stripe page can still be paid during a pause** (up to about 30 minutes). This is intended: the checklist shows such pages so you know before leaving.
- **Payments that complete during a pause create obligations.** Normally only the automatic reimbursement, but a sale can also lead to a refund or dispute while you are away. The pause does not cover this; the checklist and cover arrangements do.
- **Separate decisions:** founder email alerts, production deployment, and access for a cover person.
