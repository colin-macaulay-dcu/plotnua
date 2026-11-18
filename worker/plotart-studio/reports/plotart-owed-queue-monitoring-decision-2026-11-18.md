# PlotArt payment pilot · next decision: who monitors the amounts-owed queue, and how often

18 November 2026 · branch `plotart/managed-checkout-pilot` (PR #20) · sandbox only · **for the founder's decision**

Recommendations below are for your decision, not approval.

## 1. What reaches you today

**With email off, no alert reaches you.**
- Every founder alert goes only to the test sink, which nothing in the founder desk displays. That covers:
  - the day-5 and deadline alerts on a reimbursement;
  - "due in 7 days" and "overdue" on an amount owed;
  - "for review" on an uncertain start date;
  - a reimbursement that keeps failing.
- The only way to see them is to open the founder desk (`/admin/checkout`). It shows the same state in three places:
  - the **Processing reimbursements** table: status, due date, OVERDUE, "Day-5 alert sent", failed attempts;
  - the **Amounts owed to artists** table: outstanding, due date, *overdue*, *For review*;
  - the flag on each affected order.

The desk is accurate, but you have to look.

## 2. The clocks the review has to keep up with

| Item | Normal case | When it needs you | Deadline |
|---|---|---|---|
| **§3.3 processing reimbursement** | Automatic. In runs 33–35 it took 5–7 seconds after payment. | Only by exception: Stripe records the fee late, or the refund keeps failing (flagged after 3 failures). | **7 Irish days** from payment; day-5 alert |
| **§3.5 bank-transfer shortfall** | Always needs you: a phone call, the payee set up at your bank, and the transfer | From the day it arises | **30 Irish days**; reminder 7 days before |
| Lost-dispute commission (PA-GAA 9.1) | Needs one click (Return commission) | From the dispute closing | 30 days |
| Refund waiting for the artist's balance | Stripe retries it; the desk escalates at 7 and 30 days | If unfunded | Stripe cancels at 45 days |

## 3. Would a weekly review be enough?

**For §3.5 shortfalls: yes.**
- 30 days gives at least four weekly reviews before the deadline.
- One review always falls inside the final 7 days, while the reminder is showing.
- The tight case is a first payment to a new payee: phone call, adding the payee at your bank (with the name check), then the transfer. Even if the item is first seen at the review three weeks in, that leaves about a week, which is enough.

**For §3.3 reimbursements: no.**
- A failure or a late fee record can arise just after a review. A weekly cycle would then first show it about 7 days later, at or after the end of day 7.
- The day-5 alert exists to prevent that, but it does not reach you while email is off.
- These cases are rare, since every real sandbox payment has reimbursed itself within seconds. But the deadline is short, and a weekly review would not reliably meet it.

**For the other items: yes**, at 30–45 days.

## 4. Options

| Option | Who | How often | Meets the 7 days? | Effort |
|---|---|---|---|---|
| **A. Weekly review only** | Founder | Once a week | No: worst case is seen around day 7 | Lowest |
| **B. Twice-weekly review** (e.g. Monday and Thursday) | Founder | Every 3–4 days | Yes: the longest gap is 4 days, so an exception is seen by day 4 at the latest, with 3 days left | Two short checks a week |
| **C. Weekly review plus alerts that reach you** | Founder | Weekly, plus alerts | Yes, if the alerts arrive | A small change, and/or your approval for founder-only email (see below) |

**What option C could use:**
- **A "Founder alerts" panel in the desk.** It would list every founder alert with a count of unread items, and needs no email.
- **Founder-only email.** It would send founder alerts to your own address only. Artist and buyer messages stay in the test sink, because their addresses are not on the allowed list. The pilot already supports this: it needs the email provider configured, your explicit approval, and your address on the allowed list.

## 5. Recommendation

1. **Who:** you, as founder. You are the only person with access, and PlotArt owes the amounts.
2. **Sandbox, now:**
   - a **twice-weekly review** (option B), for example Monday and Thursday, covering both desk tables, the order flags and the pending refunds;
   - the **Founder alerts panel**, so those reviews show what the alerts would have said.
3. **Before any live use:**
   - founder alerts must reach you by email, or as a daily digest, the same day;
   - a weekly full reconciliation of the queue against your bank.
4. **When you are away for more than 3 days:**
   - switch managed checkout off for new quotes (`CHECKOUT_PILOT_ENABLED`); amounts already owed keep their deadlines;
   - or name a cover person, which would need access and a procedure.

## 6. What I need from you

- **Monitoring:** A, B or C (or another cadence), and the days.
- **Desk panel:** whether to add the Founder alerts panel now (sandbox, no email).
- **Email:** whether founder-only email alerts should be prepared for your approval before live use.
- **Absence rule:** pause checkout, or a named cover person.
