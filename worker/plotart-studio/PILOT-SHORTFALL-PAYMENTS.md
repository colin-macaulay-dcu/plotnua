# PlotArt payment pilot: paying amounts owed to artists (internal procedure, test mode)

**Internal operating procedure for the founder. Not customer-facing. It applies only once the pilot is approved for live use; in test mode nothing is paid.**

## 1. What is owed, and where to see it

The founder desk (`/admin/checkout`) has an **Amounts owed to artists** section. It lists every item PlotArt owes and has not yet fully paid:

| Kind | Arises when | How it is paid | Deadline |
|---|---|---|---|
| Processing shortfall | Stripe's processing fee plus VAT is more than the order's commission (fee model B) | Bank transfer from PlotArt | 30 Irish calendar days (sandbox rule, 18 Nov 2026): from the Irish date of Stripe's fee record; due by the end of day 30 |
| Commission shortfall | A commission refund cannot go back through Stripe, because the application fee already reimbursed processing | Bank transfer from PlotArt | 30 Irish calendar days (sandbox rule): from the Irish date of Stripe's refund record (or, flagged for review, the pilot's record of a lost dispute or a direct repayment) |
| Lost-dispute commission | Stripe closes a dispute as lost (PA-GAA 9.1) | **Return commission** button: through Stripe as far as the fee allows; any remainder becomes a commission shortfall | 30 days from Stripe's notice (PA-GAA 9.1) |

Each item shows:
- the amount, how much has been paid, and what is outstanding;
- its age and due date. Provisional dates are marked **(provisional)** until the founder's decision on the 30-day period is recorded in `DEADLINE_DECISIONS.shortfall_days` (`src/checkout.js`);
- the rule the date comes from;
- reminders already sent;
- every payment recorded against it.

The due date is fixed when the item arises. Approving or changing the configured periods later affects only new items.

**Reminders.** The sweep reminds the founder once when an item is within 7 days of its due date (`CHECKOUT_OWED_REMINDER_DAYS`), and once when it becomes overdue. In test mode, reminders go only to the test mail sink.

**Waiting reimbursements.** The **Processing reimbursements waiting for Stripe's fee record** list shows orders where Stripe has not yet recorded the fee. The sweep retries these every 15 minutes, and nothing is estimated.

## 2. Getting bank details securely

PlotArt does not ask for artists' bank details for the gallery (PA-FAA cl. 3.5). A shortfall payment is the only time PlotArt needs them, and they then exist only in PlotArt's business banking (step 8), never in PlotArt's own systems.

1. **Never** ask for, accept or store bank details by email, chat, a web form, PlotArt Studio, the payment pilot, a log, a spreadsheet or a ticket.
2. **Phone the artist** on the telephone number in their seller information (or speak in person). Ask for the account holder name and IBAN, and say what the payment is for: the order reference and amount.
3. **Enter the details directly** into PlotArt's online banking as a new payee, while still on the call. Do not write them down anywhere else.
4. **Check the name.** Use the bank's payee name check (Verification of Payee). If it reports no match or a close match, do not pay until the artist confirms by phone.
5. **Changes of account.** Confirm any change of account by calling the artist on the number already held. Never act on a change of bank details received by email, even from the artist's usual address.
6. **Recording the payment.** Record it in the founder desk with only the bank's transfer reference and the date, for example "BT-12345 on 18 Nov". The pilot refuses references that look like an IBAN or account number, and accepts no amount above what is outstanding. A reference can be recorded only once per order.
7. **Telling the artist.** Tell the artist the amount, the order reference and the transfer reference. Never include the bank details in that message.
8. **What the bank keeps.** PlotArt's bank necessarily keeps the account name and IBAN:
   - in the saved payee: **delete it** once no further payment to that artist is expected;
   - in its record of the transfer, which also appears on PlotArt's bank statements. That record cannot be deleted. PlotArt keeps the statements as accounting records for six years after the end of the year of the payment.

   Access is limited to the founder's online banking login, with the bank's own security. This is what PA-PAY cl. 9.8 and the privacy notice describe; neither may claim that PlotArt holds no bank details.

## 3. What the records keep

| Record | Holds |
|---|---|
| `checkout_owed` | Each amount owed, why, when it arose, its due date and rule, and how much is settled. The amount and due date cannot be changed. |
| `checkout_owed_payments` | Each payment: amount, method (bank transfer, Stripe application-fee refund, or moved to a direct payment), reference, who recorded it and when. Append-only. |
| `order_ledger` | A `processing_shortfall_paid` line for each bank transfer, so statements and retention see the money movement. |

None of these contain bank details: those exist only at PlotArt's bank (section 2, step 8). All are deleted with their order at the end of its retention period, and never while the order has an open dispute, an unpaid amount owed, an open flag or a pending refund.

## 4. Open decisions

- **F11 / F12.** Both periods are approved by the founder as sandbox pilot rules on 18 November 2026: 7 Irish calendar days for the processing reimbursement (PA-PAY 3.3) and 30 Irish calendar days for bank-transfer shortfalls (PA-PAY 3.5). Decisions are recorded per deadline in `DEADLINE_DECISIONS`; `CHECKOUT_DEADLINES_APPROVED` is no longer read.
- **Who monitors the queue, and how often.** For example, a weekly check of the founder desk, plus the reminders.

## 5. Recording a bank payment, a returned transfer, and overdue follow-up (sandbox rule, 18 Nov 2026)

1. Record a payment only once PlotArt's bank shows the transfer as **executed**. Enter the amount, the bank's transfer reference and the execution date (YYYY-MM-DD). The pilot stores who recorded it and when. Keep the bank's confirmation and the payee details in the bank and accounting records, never in the pilot.
2. The artist is sent one notice (test sink in the pilot) for each executed payment: amount, execution date, reference and anything still owed.
3. If the bank returns a transfer, record it with **Transfer returned…** (date and the bank's reason, no bank details). The amount is owed again, the payment stays in the history marked returned, and the due date does not change.
4. Seven days before the deadline the founder gets a reminder. If any amount is still owed after the deadline, the founder is prompted to follow up promptly (phone the artist on the number in their seller information), the order is flagged OVERDUE, and the artist is sent one overdue notice. The founder's internal target is to resolve it within 5 working days of the deadline; the artist's deadline still applies.
5. Where the start date rests on the pilot's own record rather than Stripe's (a lost dispute, a direct repayment, a refund whose success time Stripe did not give, or a fee with no recorded time), the item is marked **For review** and the founder gets one alert.
