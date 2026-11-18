# PlotArt payment pilot · next decision: traders-only eligibility (founder decision F2)

18 November 2026 · branch `plotart/managed-checkout-pilot` (PR #20) · sandbox only · **for the founder's decision**

**Status: open.** The pilot is built traders-only by default. This paper describes the options; its recommendation is not your approval. The terms remain an unissued draft. This is not legal advice: the legal points are marked for professional review.

## 1. The question

Should the managed-checkout pilot quote only artists who declare that they sell **as traders** (in the course of their business, craft or profession)? Or should it also quote artists who declare that they **do not**? If it does, buyers would be told that EU consumer rights, including the right to cancel, do not apply to their purchase.

This affects only sales through the pilot. **An artist's direct-sale route, and Founding Artist protections, are unaffected either way.**

## 2. What is built now

| Where | Current behaviour |
|---|---|
| Seller information (artist, Studio) | The artist must choose "I sell as a trader" or "I do not sell as a trader". This is a declaration; PlotArt does not decide it. |
| Quotes | A quote for an artist who declared "not a trader" is blocked: "the pilot currently quotes only sellers who do (founder decision F2)". A switch, `CHECKOUT_ALLOW_NON_TRADER_SELLERS`, would allow it. It is unset. |
| Buyer quote page | Shows "Sells as a trader: Yes" with the buyer's consumer rights, including cancellation. A "No" version exists in code, with a warning that the rights do not apply. It is used only if the switch is on. |
| Buyer terms PA-BPT 1.2 | Both options are drafted. Drafting note: "if [traders-only] stands, delete the second option". |
| Artist addendum PA-PAY 2.2 | A bracketed eligibility note: F2 traders-only, with the alternative. |
| Tests | Traders-only is tested; the "not a trader" path is covered only by the blocking check. |

## 3. The legal frame (for professional review)

- **Consumer Rights Act 2022, s.107.** Before a consumer is bound on an online marketplace, the marketplace must tell them:
  - whether the third party offering the goods is a trader, on the basis of that third party's declaration;
  - if it is not a trader, that EU consumer-protection rights do not apply.

  The CCPC's guidance for businesses says the same: an online marketplace must tell consumers whether the seller is a business or another consumer.
- **Consequence:**
  - Option A: every pilot sale is a consumer sale from a trader, and the PA-BPT cancellation and conformity sections apply in full.
  - Option B: some pilot sales would carry no consumer rights. The pilot would still have to make the s.107 disclosure.
- **For review:**
  - whether PlotArt is an "online marketplace" for s.107 in the pilot's model;
  - how far PlotArt may rely on an artist's declaration;
  - whether any EU trader-traceability duties (Digital Services Act) apply to PlotArt at its size.

## 4. Options

| | A. Traders only (as built) | B. Allow non-traders, with disclosure |
|---|---|---|
| Buyers | Same consumer rights on every pilot sale: one set of terms, one cancellation process | Some buyers have no cancellation right. They must be told plainly before paying, and the order, confirmation and terms must carry it. |
| Artists | Artists who sell only occasionally, and do not see themselves as traders, cannot use the pilot. They keep the direct-sale route. | More artists can use the pilot |
| PlotArt's work | None beyond today | Turn on the switch; keep both PA-BPT 1.2 options; add tests for the "No" path (quote, confirmation, refund wording); legal check of the disclosure |
| Risks | Artists may declare "trader" to get in without understanding the obligations: 14-day cancellation, returns, conformity | Buyer confusion, and a weaker buyer promise under the PlotArt name. An artist may declare "not a trader" while in fact trading, which shifts risk onto the buyer. |
| Pilot evidence | Matches everything tested so far | Untested end to end |

**Either way:**
- The declaration is the artist's own, kept with each quote snapshot.
- Changing it after approval requires the quote to be approved again.
- PlotArt never tells an artist which to choose.

## 5. Recommendation (for your decision, not approval)

**A, traders only, for the sandbox pilot.**
- It is what is built and tested.
- It gives every pilot buyer the same protection.
- It keeps one set of buyer terms.

Revisit B only if artists who are not traders ask to use the pilot. Get the s.107 disclosure and the declaration wording reviewed professionally before any live use.

## 6. What I need from you

1. **A or B** for the sandbox pilot.
2. **If A:**
   - delete the second option from PA-BPT 1.2 and the bracket in PA-PAY 2.2 (the draft stays unissued);
   - add a short line to the seller-information screen, explaining that non-traders cannot use the pilot and can still sell directly.
3. **If B:**
   - approve turning on the switch for the sandbox only;
   - the buyer-facing "not a trader" wording comes back to you before any test.

Sources: Consumer Rights Act 2022 s.107 (irishstatutebook.ie/2022/en/act/pub/0037/sec0107.html); CCPC guidance for businesses (ccpc.ie).
