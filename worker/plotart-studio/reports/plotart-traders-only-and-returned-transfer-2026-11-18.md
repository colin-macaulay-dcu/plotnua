# PlotArt payment pilot · traders-only managed checkout, and the returned-transfer notice

18 November 2026 · branch `plotart/managed-checkout-pilot` (PR #20) · sandbox only · **for the founder's review**

**Decisions applied:** founder decision F2, Option A (10:00, 18 November). Nothing is merged, deployed or issued, and the terms remain unissued drafts.

---

## 1. Traders-only managed checkout

### What changed

- **Scope:** managed checkout is available only to an artist who answers "I sell as a trader". The question is asked only inside the payment pilot, in the seller information an artist completes after choosing managed checkout.
- **Not affected:** gallery listing, enquiries, direct sales and the Founding 25 arrangements. No code outside the pilot reads the answer.
- **"I do not sell as a trader" or "I'm not sure":** the artist cannot approve a managed-checkout quote, and the founder cannot issue one.
- **No override:** the switch that could have let other sellers through has been removed.
- **Buyer page:** the "No" wording was removed. A buyer can only reach a quote from a declared trader.

### Studio wording (exact text, for your review)

**Above the form:**

> Not sure? You do not need to complete this form. Leave it, and keep selling directly as now. You can come back to it at any time, or leave the payment pilot.

**The question** (three radio buttons of equal weight; none pre-selected):

> **Do you sell your artwork as a trader?**
>
> This question is only about PlotArt's managed checkout, where the buyer pays through Stripe. It does not affect your gallery listing, enquiries, direct sales, or any Founding 25 arrangement.
>
> Selling as a trader means selling in the course of your business, craft or profession. PlotArt cannot decide this for you. If you are unsure, you may wish to take advice; meanwhile you can keep selling directly.
>
> ○ **I sell as a trader**
> Managed checkout is available for your sales. Your buyers have EU consumer rights against you as the seller, including the right to cancel within 14 days of receiving the artwork and return it, and your seller information is shown to them as a trader.
>
> ○ **I do not sell as a trader**
> Managed checkout is not available for your sales. You can keep selling directly, as now: buyers pay you and nothing else changes.
>
> ○ **I'm not sure**
> Managed checkout stays unavailable until you confirm. You can keep selling directly, as now, and come back to this question at any time.

**Shown when the answer is not "trader":**

> Managed checkout is not available for your sales, because you have not confirmed that you sell as a trader. Your gallery listing, enquiries and direct sales continue as before. You can change your answer at any time.

**If such an artist tries to approve a quote** (the same text, plus):

> … This quote cannot be approved for managed checkout; you can still sell this work directly.

**Buyer quote page:**

> Sells as a trader: Yes. The seller has declared to PlotArt that they sell as a trader, so your consumer rights, including the right to cancel, apply.

### Draft terms (still unissued; legal wording flagged)

**PA-PAY 2.2(d):**

> confirmation that the artist sells as a trader, that is, in the course of their business, craft or profession (clause 2.3);

**PA-PAY new 2.3** (the later clauses are renumbered 2.4 to 2.6):

> 2.3 **Managed checkout is for artists who sell as traders.** PlotArt-managed checkout is available only to an artist who confirms to PlotArt that they sell their artwork as a trader. The artist gives that confirmation, and keeps it up to date, in PlotArt Studio. PlotArt does not decide whether the artist is a trader and relies on the artist's confirmation. An artist who does not sell as a trader, or is not sure, cannot use managed checkout, but this does not affect their gallery listing, enquiries, direct sales or any Founding 25 arrangement, and they may continue to sell directly. When an artist sells through managed checkout as a trader, the buyer has the consumer rights set out in the buyer purchase terms (PA-BPT), including the right to cancel, and the artist as seller is responsible for honouring them. [For professional review before live use: the definition of trader, reliance on the artist's confirmation, and the marketplace information duty under the Consumer Rights Act 2022, s.107.]

**PA-BPT 1.2:**

> 1.2 **The seller is a trader.** The seller has declared to PlotArt that they sell as a trader, in the course of their business, craft or profession. PlotArt offers its managed checkout only to sellers who have made that declaration. As a consumer buying from a trader, you have the consumer rights that arise from EU consumer protection law, including the right to cancel described in section 6. [For professional review before live use: the s.107 Consumer Rights Act 2022 information and reliance on the seller's declaration.]

## 2. Returned-transfer notice (§3.5)

When a bank transfer recorded as paid is returned:
- the artist gets **one** correction notice, in the test sink;
- the amount is owed again, and the original due date is kept.

Repeat requests to record the same return are refused, and later sweeps send nothing more. Outbound artist email is off: the notice is recorded as `held_in_test_sink`.

**Notice, before the deadline** (generated text):

> Subject: PlotArt payment pilot · ‹order› · correction: a bank transfer to you was returned
>
> Order ‹order›
>
> Correction: a bank transfer that PlotArt recorded as sent to you has been returned to PlotArt by the bank.
>
> Returned payment: EUR 3.83, sent by bank transfer on Wednesday 18 November 2026 (PlotArt's transfer reference: SIM-TRF-0002), returned on Wednesday 18 November 2026. The bank gave this reason: SIMULATED: beneficiary account closed.
>
> PlotArt still owes you EUR 3.83 on this order. The date it is due is unchanged: the end of Thursday 17 December 2026 (Irish time).
>
> PlotArt will phone you to check the account details before sending it again. PlotArt will never ask for your bank details by email.
>
> This message comes from the PlotArt payment pilot (test mode).

**If the return comes after the deadline**, the fourth paragraph reads:

> PlotArt still owes you EUR 6.83 on this order. The date it is due is unchanged: the end of Sunday 15 November 2026 (Irish time), so it is now overdue. We are sorry for the delay.

**Decision for you:** the notice passes on the bank's reason for the return word for word. Tell me if you would rather leave the reason out.

## 3. Results

### Real Stripe sandbox — run 35

[Run 44281859586](https://github.com/colin-macaulay-dcu/plotnua/actions/runs/44281859586): approved, job 10:05:40–10:06:54 UTC, **conclusion: success**. Every check passed.

| Check | Result | Evidence |
|---|---|---|
| **E22** traders only | **PASS** | The artist answered "I'm not sure". Approving the quote was refused (409) with the Studio wording above, and issuing it was refused (409). `checkout_available` was false. There was no checkout session, and the checkout Worker made **0** Stripe calls. |
| **E21a/b** normal paid path | **PASS** | €200 payment. Stripe's fee of €6.55 plus VAT of €1.51 makes €8.06, reimbursed at 10:06:46 (`fr_1Ud5lJHx1Olx8cdw6UICsDOy`). |
| **E21c** artist credit | **PASS** | Exactly one match on the artist's balance: +€8.06 (806 cents), EUR, `adjustment` on the charge, created 10:06:46, pending, available 25 Nov. |
| **E21e** clock start | **PASS** | Success event at 10:06:40 (used); charge at 10:06:39, 1 s earlier; both on 18 Nov in Ireland. |
| **E21f** run 33 re-read | **PASS** | Still exactly one matching credit. |
| E21d, E17b–d | **PASS** | The runtime key still has five permissions and was the only key used. |

### Local tests: mock Stripe, with SIMULATED dates, returns and bank reasons

230/230 checks pass; migration 9/9; deployment tooling 23/23.

**Traders only:**
- **SP5:** an artist who answers "not a trader" is not quoted.
- **SP5b:** "I'm not sure" is accepted but keeps checkout unavailable. Three neutral choices, the wording above, and an unknown answer is refused.
- **SP6:** once the artist answers "trader", the quote is issued and checkout is available.

**Returned transfer:**
- **SD19:** the €3.83 is restored and the history is kept.
- **SD19b:** exactly one correction notice, with the returned payment, the €3.83 still owed and the unchanged due date of 17 December. It is held in the test sink, and repeats and sweeps add nothing.
- **SD24:** a return after the deadline gives one notice saying the amount is now overdue. No second overdue notice is sent, and the due date is unchanged.

Run 35 ran on the commit before a one-character fix: a full stop after the bank's reason. That change touches no Stripe call and was re-checked locally (230/230).

## 4. Still needs live verification

1. **Professional legal review:** the definition of trader, reliance on the artist's declaration, and the s.107 marketplace information duty. This must happen before live use.
2. **Real bank transfers:** executed, partial and returned transfers, and bank reasons, are simulated. Live use needs a real transfer, and ideally a real return, checked against the records.
3. **Email delivery:** every artist and founder notice so far has gone only to the test sink. Live email is off and unapproved.
4. **A real shortfall:** no sandbox sale has produced one, so the 30-day rule has local evidence only.
5. **Insufficient platform funds:** still open before live use.
6. **The extension for a late fee record (§3.3):** simulated only. Stripe has recorded the fee instantly in every real run.
