# PlotArt payment pilot · monitoring, founder alerts panel, absences and an email-alert proposal

18 November 2026 · branch `plotart/managed-checkout-pilot` (PR #20) · sandbox only · **for the founder's review**

Nothing is merged or deployed. Outbound email stays off.

---

## 1. Decision recorded: monitoring, Option B (sandbox)

**Who:** the founder.

**When:** every Monday and Thursday at the checkout desk (`/admin/checkout`). Each review covers:
- **Founder alerts**: open items first;
- **Processing reimbursements**;
- **Amounts owed to artists**;
- **flagged orders** (the flag on each order card);
- **refunds waiting** for an artist's Stripe balance.

**Next actions:** for anything approaching its deadline, record the next action and a follow-up date against its alert. The panel marks it **Follow-up due** from that date, even between reviews, until the item is resolved.

## 2. Founder alerts panel (new, top of `/admin/checkout`)

- **Source:** the existing founder alert records, that is, the founder's copies of the alerts in the pilot's test inbox. No new alerts are generated.
- **Header:** "Founder alerts · N unread · N open · N follow-ups due", then:

  > Sandbox: these alerts were recorded in the test inbox only and were not emailed to you. Review them at the Monday and Thursday checks. Marking an alert read does not resolve the item behind it.

- **Each alert shows:**
  - read or unread, and open or resolved;
  - when it was recorded (Irish time), with "Sandbox: recorded in the test inbox only. Not emailed to you (outbound email is off).";
  - the reason, with the first line of the alert;
  - a link to the order;
  - **the amount outstanding now**, the **Irish due date** (OVERDUE where it applies), and the next action with its follow-up date.
- **Open/resolved is recalculated from the order on every view.** Marking an alert read changes only its read state. An amount stays outstanding until the issue behind it is resolved.
- **Layout:** open items are listed first, with follow-ups due at the top. Resolved items are collapsed underneath.
- **Access:** founder only. An artist's request is refused, and bank details are refused in the next-action field.

Screenshot: `reports/founder-alerts-panel-2026-11-18.png` (local test data, simulated).

## 3. What `CHECKOUT_PILOT_ENABLED` does

The pilot switch was checked in the code (`requireOn` and the routes that call it).

| When the switch is OFF | Effect |
|---|---|
| New orders, sending to the artist, artist approval, issuing quotes | **Blocked** |
| Artists joining, onboarding, processing consent | **Blocked** |
| A quote already issued: the buyer's quote page and "Pay" | **Blocked.** The page says "Payments are not open". The quote stays issued until it expires; it is not cancelled. |
| A Checkout Session already open at Stripe | **Not stopped.** It stays payable at Stripe until it expires (about 30 minutes). A payment made there is still recorded by Stripe's signed event. |
| Stripe events (payments, refunds, disputes) | **Still processed** |
| 15-minute sweep: processing reimbursements, fee re-reads, alerts, reminders, pending-refund checks, message retries | **Still runs** |
| Founder "Reconcile processing fee", recording bank transfers and returns, cancelling quotes, fulfilment, holds, the alerts panel | **Still work** |
| **Founder refund to a buyer** | **BLOCKED** |
| **Return commission after a lost dispute** | **BLOCKED** (it uses the same refund action) |
| **Founder "Reconcile" of a checkout after an interruption** | **BLOCKED** |

**⚠ Flag:** the switch **does interrupt repayment and reconciliation.** With it off, you could not:
- refund a buyer;
- return commission after a lost dispute, which is due within 30 days under PA-GAA 9.1;
- reconcile an interrupted checkout.

**I do not recommend using `CHECKOUT_PILOT_ENABLED` to cover an absence.**

**Alternative, not built, for your decision:** a separate **"pause new quotes"** setting that blocks only:
- new orders;
- issuing quotes;
- starting a payment on a quote not yet paid.

Everything else would stay on: refunds, commission returns, reconciliation, the sweep and Stripe events.

### Spotting obligations that need attention during an absence

Before leaving, and on return:
1. **Founder alerts:** sort by open, then follow-ups due. Set a next action and follow-up date on anything falling due while you are away.
2. **Processing reimbursements:** anything still "Waiting for Stripe" or "Fee known · outstanding", and its Irish due date (7 days).
3. **Amounts owed to artists:** any item due within your absence, plus 2 working days. Pay it before you leave if it is already known.
4. **Refunds waiting:** "Stripe cancels it on" dates.
5. **Order flags:** lost disputes (commission due within 30 days), failed refunds, failing reimbursements, undelivered messages.
6. **Quotes issued and still open:** cancel or let expire. Under the alternative pause, a quote that is already issued could not be paid while you are away.

The 15-minute sweep keeps reimbursing automatically while you are away. Only exceptions wait for you.

## 4. Proposal for separate approval: same-day founder email alerts before live use

**Not enabled.** Outbound email stays off.

- **Recipient:** one founder address only, yours, to be confirmed by you. It is set as the founder notification address and is the only entry on the allowed-recipient list. Artist and buyer messages cannot be sent externally, because their addresses are not on the list. Reply-to: hello@plotnua.ie.
- **Triggers (same day):**
  - reimbursement day-5, deadline, extended and fee-time-unknown alerts;
  - **a reimbursement failing after 3 attempts** (today a flag only; an alert would be added);
  - an amount owed due within 7 days, or overdue;
  - "for review" start dates;
  - a refund waiting at 0, 7 and 30 days, or failed;
  - a dispute lost (commission to return);
  - a message that could not be delivered after 6 attempts;
  - **plus one daily digest** at 08:15 Irish time, only if anything is open or a follow-up is due.
- **Content rules:**
  - order reference, reason, amount and Irish due date, with a link to the desk;
  - never bank details;
  - no buyer contact details.
- **Panel continuity:** every emailed alert is also recorded for the panel, so the panel stays complete when email is on. This is a small change, made only with the email approval.
- **Test plan:**
  1. **Local:** every combination of mail settings (not configured; configured but not approved; approved with an address not on the list; approved and on the list) must give the expected result. Artist and buyer messages never leave the test inbox. Each alert is sent once (idempotency key), and a failed send is retried and shown in the panel.
  2. **Sandbox, one approved run:** trigger each alert type with simulated dates, then confirm receipt in your inbox and the time against the panel.
  3. **Switch-off check:** unsetting `CHECKOUT_MAIL_APPROVED` returns everything to the test inbox at once.
  4. **Results reported** before any live use.

### Weekly reconciliation against the bank (proposed, every Monday review)

1. Export the week's transactions from PlotArt's business bank.
2. **Match each recorded transfer** to the bank entry by reference, amount and execution date:
   - a bank entry not recorded in the pilot: record it;
   - a recorded transfer the bank does not show as executed: investigate;
   - a return in the bank: record it with "Transfer returned…".
3. **Stripe:** for each order, compare the application fee refunds Stripe shows with the reimbursements in the ledger.
4. **Record** the reconciliation date and result as a next action on the panel, or in a short log.
5. **Optional, not built:** a desk export of the bank transfers recorded in the last 7 days, for the match in step 2.

## 5. Results (local tests: mock Stripe, simulated data)

235/235 checks pass; migration 9/9 (now 23 pilot tables); deployment tooling 23/23.

| Check | What it proves |
|---|---|
| AP1 | The panel lists founder alerts with the unread count, reason, current amount, Irish due date, order link and sandbox wording |
| AP2 | **Repeated checks:** two views and two sweeps create no new alerts and change no counts |
| AP3 | **Marking read:** unread falls by one, but the item stays open with €6.83 still owed. The next action and follow-up date are saved and shown as due. Bank details are refused, and an artist cannot use the panel. |
| AP4 | **Resolving the item:** after the €6.83 is paid, the same alert shows Resolved / "Nothing outstanding: paid", keeps its read state and next action, and the follow-up is no longer due. It can be marked unread again. |

No real Stripe run was needed: the panel reads only the pilot's own records and makes no Stripe call.

## 6. Next decision

**How to cover an absence of more than three days**, now that the pilot switch is known to block refunds, commission returns and reconciliation. Choose between:

1. a narrow **"pause new quotes"** setting, built and tested on the branch (as in section 3); or
2. no pause, with the absence checklist above only; or
3. a named cover person, with desk access and a short procedure.

The email-alert proposal (section 4) is a separate approval and can wait until before live use.
