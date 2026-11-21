# PA-BBT-2026-11 and PA-BAA-2026-11 — r1 review notes (21 November 2026)

Not part of either text. Lists what needs legal review, what is new compared with the issued texts, and what the code must do before the texts can be issued.

## A. Founder decision applied (not to be reopened)

- Founding 25: PlotArt charges 0% commission during the agreed commission-free period. The artist bears Stripe's actual processing fee on those payments, only with explicit, separate, revocable opt-in consent (PA-BAA 3.4, 4). Approved by the founder 21 Nov 2026.
- Gallery Artists: 15% under PA-GAA cl. 5, with PlotArt reimbursing Stripe's processing fee (Fee Model B, PA-PAY 3.3–3.5) so the combined deduction never exceeds commission. No commission on delivery. No buyer fees.

## B. Existing commitments preserved

| Commitment | Where it lives | How the drafts keep it |
|---|---|---|
| Founding Enquiries commission-free permanently; commission only by expressly accepted separate terms | PA-FAA 5, 6 | PA-BAA 0.2(a), 3.1, 3.2, 4.4 |
| No compulsory fees, ever; no change may introduce one | PA-FAA 3, 13.2 | PA-BAA 0.2(a), 0.3(b), 3.4(a), 4.2; basket and consent optional and revocable |
| Gallery Artist keeps ≥85% of Commission Base; combined deduction ≤ commission | PA-GAA 5; PA-PAY 0.2(b), 3.3 | PA-BAA 0.2(b), 3.3 |
| No commission on delivery etc. | PA-PAY 3.1 | PA-BAA 0.2(c), 3.1 |
| Artist is seller; PlotArt not seller, no escrow | PA-PAY 2, 5.2; PA-BPT 1.3, 3.1 | PA-BAA 2, 6.5; PA-BBT 1.3, 4.1 |
| Buyer consumer rights, refunds, pending/failed refunds | PA-BPT 6–8 | PA-BBT 7–9 (per artwork) |
| Transit insurance ≥ price, carrier liability alone not accepted | PA-PAY 6.2 | PA-BAA 5.1(d), 8.2 |
| €10k linked-purchase limit, €9,999.99 per artwork | PA-PAY 1.4; PA-BPT 4.4 | PA-BBT 3.3; PA-BAA 1.3 |
| Records and retention | PA-PAY 8; PA-BPT 9 | PA-BAA 9; PA-BBT 10 |
| Fresh live acceptance | PA-PAY 10 | PA-BAA 12 |
| Issued texts unchanged | — | PA-BPT and PA-PAY untouched; PA-PAY 1.3 disapplied for basket orders only (PA-BAA 0.4) |

## C. Provisions requiring legal review

1. **PA-BAA 0.2(a), 3.4, 4 — Founding processing fee vs PA-FAA cl. 3 and 13.2.** Confirm that an optional, revocable consent under which Stripe (not PlotArt) deducts its own fee is not a "compulsory fee" or a "change" requiring cl. 6.4 acceptance, and that the 0% commission promise is not undermined.
2. **PA-BAA 0.4 — incorporating PA-PAY clauses by reference** for artists who have not accepted PA-PAY, and disapplying PA-PAY 1.3 for basket orders only. Confirm this works as a variation (PA-GAA 13) and as stand-alone terms for Founding Artists.
3. **PA-BAA 5.2 — standing delivery offer replaces per-quote approval.** The artist is bound to sell to any basket buyer at the gallery price. Confirm this is acceptable as the artist's offer, and that PA-GAA 4.2 is properly varied.
4. **PA-BBT 7.2 / PA-BAA 2.3(b) — cancellation period runs from the last artwork received.** Deliberately buyer-favourable, to cover the "multiple goods in one order" rule (CRD art. 9(2)(b)(i)) in case the basket is treated as one order. It extends each artist's exposure. Confirm or shorten.
5. **PA-BBT 4.2 — statement-line disclosure.** The terms disclose separate card payments per artwork (required for transparency and to reduce chargebacks). The approved confirmation page wording does not mention it. Confirm that disclosure in the terms and confirmation emails is enough, or whether a short line is needed before payment.
6. **PA-BBT 3.2 — when the contract is made** (on capture of all payments). Confirm against the authorise-then-capture flow and the "order with obligation to pay" button requirement (CRD art. 8(2)); the button reads "Checkout" and Stripe's page shows the payment. Adviser may require the final button to read "Buy now" or "Order with obligation to pay".
7. **PA-BBT 4.6, 10.2(b); PA-BAA 6.1(a), 9.1(c) — saving and cloning the card.** Confirm PSD2 / SCA treatment of off-session merchant-initiated payments after a setup-mode Checkout, and the privacy notice basis for PlotArt's platform holding the payment method. Privacy notice section "The PlotArt payment pilot" must be updated before issue.
8. **PA-BAA 6.4 — partial capture.** New commitment: if some payments are taken and another cannot be, the buyer may cancel at no return cost before dispatch, and commission is returned in full. Confirm.
9. **PA-BBT 6.2 — late delivery.** Restates CRD art. 18 in a buyer-friendly form. Confirm.
10. **PA-BAA 3.5 — PlotArt reimburses any fee on uncaptured authorisations.** Confirm whether Stripe charges any; the commitment is open-ended.
11. **AML / €10k cap and VAT** (carried from the production audit): confirm the linked-purchase rule is operational only, and the VAT position of the application fee for Founding (nil) and Gallery orders.

## D. Code that must match the texts before issue (not done; no deploy)

1. **Pre-payment seller disclosure (blocker).** The basket page shows only "by <artist>". PA-BBT 1.1 and consumer law require, before payment, each seller's legal name, address, email, phone and VAT number, and the return cost (PA-BBT 7.4(c)). Add a compact "Seller and returns" line or expandable per artwork, without changing the approved page structure.
2. **Processing consent (blocker for Founding lines).** `lineFor` checks `mem.processing_consent`, but `artistMembership` never sets it and there is no consent record. Add a separate append-only consent/withdrawal record with the PA-BAA 4.5 statement, a Studio control, and set `BASKET_DECISIONS.commission_free_lines_live` to `'with_processing_consent'`.
3. **Last-delivery date for the cancellation period** (PA-BAA 2.3(b)): show the basket's last delivery date to each artist in Studio.
4. **Install the texts:** build fingerprinted HTML, add to `LIVE_BASKET_DOCS`, and install `basket_terms` rows by an approved migration after 0019.
