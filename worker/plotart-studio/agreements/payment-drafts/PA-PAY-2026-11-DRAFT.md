# PlotArt Payment Pilot Addendum — PA-PAY-2026-11 (DRAFT r4, 17 November 2026)

**Status: draft for founder review. Not issued. Not accepted by any artist. Not installed in PlotArt Studio.**
It can be accepted only after Colin approves the text, it is issued as fingerprinted HTML in
`agreements/payment-issued/`, and an approved migration installs it in `payment_terms`.

r4 changes (from Stripe test-mode results, 17 Nov 2026): Stripe's processing fee and any VAT on it shown as separate
lines, with VAT conditional on where the artist's Stripe account is based and their own VAT position (cl. 3.4–3.4A);
dispute fees split into the received fee and the countered fee (cl. 7.2); refunds when the balance is low restated to
match observed behaviour, with the fully unfunded case marked unverified (cl. 7.3); a refund Stripe reverses after
confirming it (new cl. 7.3A).
r3 changes: separate consent for the processing charge on commission-free orders, with direct payment kept as the
normal route (cl. 3.6); how to fund a refund after payout and the escalation timeline (cl. 7.3); retention periods with
their start dates and legal holds (cl. 8.1). r2 changes: card-fee examples and refund/dispute costs added (cl. 3, 7); confirmed transit insurance required for every
shipment (cl. 6); refunds when the Stripe balance is too low (cl. 7.3); who carries which loss separated from what the
artist owes the buyer (cl. 7.6–7.7); value limit and linked purchases explained without any claim about legal effect (cl. 1.4).

This addendum is optional. It sits beside the artist's existing PlotArt agreement (PA-FAA-2026-11 Founding Artist
Agreement or PA-GAA-2026-11 Gallery Artist Agreement) and the Gallery Publication and Image Licence. It changes none of
them. Where this addendum and the artist's agreement differ, the term more favourable to the artist applies.

## 1. What the pilot is
1.1 For a sale PlotArt has introduced, the artist may let the buyer pay by card through a secure, Stripe-hosted
checkout, after the artist and the buyer have agreed the artwork, its price and its delivery.
1.2 Taking part is optional. Direct enquiries and direct sales continue exactly as before. The artist can leave the
pilot at any time in PlotArt Studio; quotes not yet paid are then cancelled, and paid orders are completed.
1.3 The pilot covers one original artwork by one artist per order, in euro. It does not cover prints, commissions of
new work, hire, multi-artwork baskets, discounts, gift cards or instalments.
1.4 During the pilot, PlotArt quotes artworks priced up to EUR 9,999.99, and will not quote a purchase that would bring a
buyer's apparently linked purchases through the pilot (by the same buyer, or by anyone PlotArt knows to be acting with
them) to EUR 10,000 or more in twelve months. These are limits on the scope of the pilot. They are not a statement about
anyone's legal obligations.

## 2. The artist is the seller
2.1 The artist is the seller of the artwork and contracts with the buyer. PlotArt introduces and coordinates; it is not
the seller and does not take ownership or possession of the artwork.
2.2 Payment is made to the artist's own Stripe account, which the artist opens through Stripe's hosted onboarding.
Stripe's own terms (the Stripe Connected Account Agreement) apply between the artist and Stripe. PlotArt never sees the
artist's identity documents or bank details.
2.3 The artist authorises PlotArt to create, for an order the artist has approved, a hosted checkout on the artist's
Stripe account for exactly the approved amounts, and to receive PlotArt's commission (if any) from that payment as a
Stripe application fee.

## 3. Charges, fees and tax
3.1 **PlotArt commission.** Exactly as the artist's existing agreement provides, and nothing more:
  (a) an enquiry introduced during a Founding Artist's founding year is commission-free permanently, whenever the sale
      completes (PA-FAA-2026-11 cl. 5);
  (b) a Founding Artist owes commission only under commission-bearing terms they have separately and expressly
      accepted, in effect when the enquiry was introduced (PA-FAA-2026-11 cl. 5–6). This addendum is **not** such terms;
  (c) a Gallery Artist owes the rate in their Gallery Artist Agreement (standard 15%, including any VAT that applies to
      it), on the Commission Base only (PA-GAA-2026-11 cl. 5).
3.2 Commission is never charged on delivery, packing, transport, insurance, installation or import costs.
3.3 **Stripe's processing fees are separate from PlotArt's commission.** Stripe charges them to the artist's Stripe
account on every payment, including commission-free ones, on the whole amount the buyer pays (artwork and delivery).
They are Stripe's fees, not PlotArt's, so they are not part of the 15% and do not count towards the "at least 85%" in
PA-GAA cl. 5.2, which concerns PlotArt's commission only. [Founder decision D1: confirm the artist bears these fees, or
adopt the assessed alternative in which an accepted commission is the artist's total deduction and PlotArt absorbs
Stripe's fee out of that commission (spec, "Fee model assessment"). Not adopted.]
3.4 **Examples** (illustration only; EUR 1,000 artwork + EUR 75 delivery and insurance = EUR 1,075. Stripe fees use
Stripe's published standard pricing for EEA businesses at the time of writing — standard EEA cards 1.5% + €0.25, premium
EEA cards 1.9% + €0.25, UK cards 2.5% + €0.25, international cards 3.25% + €0.25 — to be re-checked when issued. Stripe's
fee is shown before any VAT; VAT on it is a separate line because it does not apply in the same way to every artist,
see 3.4A):

| | Founding Artist, commission-free | Gallery Artist, 15% |
|---|---|---|
| Buyer pays | €1,075.00 | €1,075.00 |
| PlotArt commission (application fee) | €0.00 | €150.00 (incl. any VAT) |
| Stripe processing fee, standard EEA card (before any VAT) | €16.38 | €16.38 |
| VAT on Stripe's processing fee, **if it applies** (3.4A) | Irish-based Stripe account: €3.77 (23%); otherwise see 3.4A | Irish-based Stripe account: €3.77 (23%); otherwise see 3.4A |
| Reaches the artist's Stripe balance | €1,058.62, less any VAT on Stripe's fee (Irish-based account: €1,054.85) | €908.62, less any VAT on Stripe's fee (Irish-based account: €904.85) |
| Paid by the artist to the transporter/insurer as quoted | €75.00 | €75.00 |
| Left for the artwork | €983.62, less any VAT on Stripe's fee (Irish-based account: €979.85) | €833.62, less any VAT on Stripe's fee (Irish-based account: €829.85) |

Other cards, Stripe processing fee before any VAT (and, for an Irish-based Stripe account, VAT at 23%): premium EEA card
€20.68 (+ €4.76); UK card €27.13 (+ €6.24); international card €35.19 (+ €8.09).
[Evidence note, not for issue: in Stripe test mode on 17 Nov 2026 an Irish test card on this sale showed €16.38 + €3.77
VAT + €150.00 application fee, net €904.85, matching the Gallery Artist column for an Irish-based account. A US test card
showed €34.11 + €7.85, below the published international rate; test-mode fees are not live pricing.]
3.4A **VAT on Stripe's fees** is between Stripe and the artist and depends on the artist, not on PlotArt:
  (a) for Stripe account holders based in Ireland, Stripe states that VAT applies to all Stripe fees at the standard rate,
      added on top of the fees, with a monthly tax invoice from Stripe;
  (b) for Stripe account holders elsewhere in Europe, Stripe states that it supplies its services from Ireland without
      charging VAT on its fees, and the account holder may need to account for VAT under the reverse charge;
  (c) whether any VAT on Stripe's fees is a final cost to the artist depends on the artist's own VAT position (for example
      whether they are registered and can recover it). PlotArt does not give tax advice; artists should check with their
      own adviser. The figures in 3.4 for an Irish-based account assume the VAT is not recovered.
3.5 The artist remains responsible for any VAT or other tax on the sale of the artwork, and for their own invoice or
receipt to the buyer where required.
3.6 **Commission-free orders and direct payment.** Where PlotArt takes no commission on an order (every Founding
Enquiry, and Founding Artists without separately accepted commission terms), Stripe's processing fees would be the only
deduction. Selling directly, with the buyer paying the artist and no deduction at all, remains the artist's normal route.
Such an order can be paid through the pilot only if the artist has given a separate, explicit consent to the processing
charge in PlotArt Studio. That consent is not part of accepting this addendum, can be withdrawn at any time, and
withdrawing it cancels any unpaid commission-free quote.

## 4. Quotes, approval and reservation
4.1 PlotArt prepares a quote showing the seller, the artwork, its price, every delivery charge, the delivery and
insurance arrangements, and the commission (if any) with the basis for it.
4.2 Before any buyer can pay, the artist confirms that the work is available and not promised elsewhere, and confirms
its location, condition, framing and glazing, dimensions and weight, and the packing, transport and insurance
responsibilities shown. The artist approves that exact quote version. Any later change creates a new version that
needs the artist's approval again.
4.3 While a buyer is in checkout the work is reserved for a short, stated period. The artist will not sell or promise it
elsewhere during an open quote, and will record any outside sale in PlotArt Studio straight away.

## 5. Payment, payout and no escrow
5.1 Only a payment confirmed to PlotArt directly by Stripe completes an order. PlotArt then marks the work sold in
PlotArt Studio and tells the artist.
5.2 Payouts from the artist's Stripe balance to their bank follow the payout schedule of the artist's Stripe account.
PlotArt does not hold the money, does not delay payouts until delivery and does not offer escrow.

## 6. Delivery and insurance
6.1 Each quote names who packs, who books and contracts with the transporter, who pays for transport, who arranges
installation and who bears any import costs, with the transporter's shipment-specific confirmation.
6.2 **Every shipment in the pilot must have transit insurance confirmed for that shipment**, covering at least the
artwork price from collection to signed delivery. The quote names the insurer, who holds the cover, the covered value
and valuation basis, any excess and main exclusions, the period and the claims contact, with a confirmation reference.
Carrier's limited liability alone, or no cover, is not accepted in the pilot. The insurance confirmation is recorded in
PlotArt Studio before dispatch.
6.3 The seller dispatches as quoted and records dispatch and delivery evidence (tracking, signed receipt, condition
photographs) in PlotArt Studio.
6.4 The buyer's statutory rights do not depend on any carrier or insurance claim being made or completed.

## 7. Refunds, returns and disputes
7.1 As seller, the artist handles cancellations, returns and refunds under consumer law. PlotArt can issue a refund
from the order on the artist's instruction or with the artist's agreement.
7.2 Refunds and disputed amounts are debited from the artist's Stripe balance by Stripe. Stripe does not return its
processing fee on the original payment when a payment is refunded. A dispute (chargeback) also carries Stripe's dispute
fees, charged to the artist's Stripe account (Stripe's published EEA pricing at the time of writing, to be re-checked
when issued, before any VAT under 3.4A): a **dispute received fee** of €20 for each dispute, which is not returned even
if the dispute is won; and, if the dispute is responded to with evidence, a **dispute countered fee** of €20, which
Stripe returns if the dispute is won. For an Irish-based Stripe account VAT is added to these fees (test mode showed
€24.60 for the received fee: €20 + 23%). [Founder decision D4: whether artists respond to disputes themselves only
(cl. 7.5) or PlotArt may submit evidence for them, given the countered fee.]
7.3 **If the artist has already been paid out and their Stripe balance is too low**, Stripe may complete the refund at
once by drawing on payments not yet available to the artist, which can leave the artist's Stripe balance negative (seen
in test mode); or it may hold a card refund as pending until the balance can cover it, may debit the artist's bank
account where Stripe's terms allow, and cancels the refund if it is still pending after 45 days. [Unverified: what
Stripe does when the available and incoming balance together cannot cover the refund was not reproducible in test mode
with the pilot's permissions; confirm before issue.] PlotArt tells the artist and the buyer the same day. The artist funds the
refund in one of these ways: (a) let Stripe complete it from new sales or by debiting the linked bank account; (b) add
funds to their Stripe balance (Stripe Dashboard → Balances → Add to balance, by bank transfer), which releases the refund
when the funds arrive; or (c) only after Stripe has cancelled the refund, repay the buyer directly and send PlotArt the
confirmation. The artist must not repay the buyer outside Stripe while a Stripe refund is still pending. PlotArt
reminds the artist after 7 days and escalates after 30 days. The artist remains responsible for repaying the buyer.
7.3A **A refund Stripe reverses after confirming it.** Rarely, a refund that Stripe first confirmed fails later (for
example because the buyer's card was closed). The money then returns to the artist's Stripe balance and the buyer has
not been repaid. PlotArt tells the artist and the buyer, and the artist repays the buyer once, by one route only: a new
refund through PlotArt, or a direct repayment that the artist confirms to PlotArt with evidence. Any commission PlotArt
already returned for the reversed refund stays with the artist and is not returned a second time when the buyer is repaid.
7.4 PlotArt returns its commission exactly as the artist's agreement requires, once the buyer's refund has actually
succeeded: in full for a full refund or a lost dispute, and in proportion to the artwork amount kept for a partial
refund (PA-GAA-2026-11 cl. 9). Refunds of delivery charges do not change commission.
7.5 The artist responds to any dispute in their own Stripe Dashboard; PlotArt provides the order record, quote, terms
acceptance and delivery evidence it holds.
7.6 **Who carries a loss with Stripe** is set by the account configuration: Stripe, not PlotArt, is responsible for
any negative balance on the artist's Stripe account that cannot be recovered, and recovers it from the artist under
Stripe's own terms. That arrangement is between Stripe and the artist.
7.7 **What the artist owes the buyer** does not depend on 7.6: as seller, the artist is responsible to the buyer for the
artwork, its delivery and any refund the law or the sale requires. PlotArt's own responsibilities are those it has as
the platform that introduced the sale and prepared the quote (for example, giving accurate information about the
seller and the charges); they are not the seller's.

## 8. Records and data
8.1 PlotArt keeps the order record, quote versions, approvals, payment events, ledger, refunds and delivery evidence of
an order that moved money until 31 December of the sixth year after its last payment or refund (tax record-keeping and
the limitation period for contract claims), and those of an order that was never paid for two years after it ended;
then deletes them. Opt-in and consent records are kept for six years after the artist leaves the pilot. Records are kept
longer only under a legal hold for a stated reason (for example a dispute, claim or Revenue enquiry), reviewed at least
every 12 months and released when no longer needed. These records are kept separately from the artist's gallery records, so they
remain available for refunds and reconciliation even after the artist leaves PlotArt.
8.2 PlotArt shares with Stripe only what is needed to create the artist's account and the checkout (the artist's
Studio email address and country; the buyer's email address). The buyer's details are shared with the artist only as
needed to complete and deliver the sale.

## 9. Test mode
9.1 During the test-mode pilot no real payment is taken. Moving to live payments needs a new version of this addendum
or a written confirmation, and the artist's express acceptance.

---
Founder decisions open: D1 (who bears Stripe processing fees, including on the delivery portion); D2 (whether PlotArt
issues any receipt to buyers); D3 (retention periods, with the accountant); D4 (who responds to disputes, given the
countered fee); D5 (whether PlotArt's commission refund after a lost dispute is automatic or a founder action). Professional advice outstanding: marketplace
and consumer responsibilities, commission VAT treatment, DAC7 applicability, anti-money-laundering position (see the
spec, "Anti-money-laundering").
