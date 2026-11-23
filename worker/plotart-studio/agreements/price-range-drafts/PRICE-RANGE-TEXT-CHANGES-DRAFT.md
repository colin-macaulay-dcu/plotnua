# DRAFT · Agreement changes for an open price range (prepared 23 Nov 2026)

**Status: DRAFT for founder review. Not issued, not installed, not shown to anyone.** The issued 2026-11 texts stay in force,
unchanged, until new versions are approved and issued. Nothing here takes effect by being in the repository.

## Why new versions are needed

Four issued texts state the EUR 9,999.99 per-artwork limit and/or the EUR 10,000 linked-purchase limit:

| Text | Clause | Who accepted it |
|---|---|---|
| PA-PAY-2026-11 · Payment Pilot Addendum | 1.4 | artists (Studio) |
| PA-BPT-2026-11 · Buyer Purchase Terms | 4.4 | buyers (single-artwork quotes) |
| PA-BAA-2026-11 · Artist Basket Addendum | 1.3 | artists (Studio) |
| PA-BBT-2026-11 · Buyer Basket Terms | 3.3 | buyers (basket) |

A text that someone has accepted never changes under its identifier, so an open price range needs **new identifiers**
(proposed: PA-PAY-2026-12, PA-BPT-2026-12, PA-BAA-2026-12, PA-BBT-2026-12), with **every other clause carried over word for
word**. The code opens the range only when none of the current texts is a 2026-11 text (`rules.priceRange`), so issuing the new
texts is a precondition, not a side effect.

**Artists must accept the new PA-PAY and PA-BAA in Studio.** Until an artist does, the readiness check treats their
acceptance as of an old version ("old" on the Basket readiness tab) and their works are not offered online. Plan the
switch-over with artists before issuing.

## Two variants of the linked-purchase wording

The per-artwork ceiling can simply go. The **EUR 10,000 linked-purchase wording depends on the anti-money-laundering advice**
(see `AML-LEGAL-BRIEFING.md`). Two variants are drafted; only one is issued.

- **Variant 1 (interim, no AML procedures yet):** the per-artwork ceiling is removed, the EUR 10,000 linked-purchase limit
  stays. In practice almost nothing changes for buyers (a single work at EUR 10,000 or more still cannot be bought online),
  so Variant 1 is worth issuing only if it is a deliberate interim step.
- **Variant 2 (after advice, with procedures in place):** no price limit; PlotArt may verify identity and ask for
  information before a purchase of EUR 10,000 or more (alone or linked) can be completed, and may decline a purchase it
  cannot lawfully complete, without charging. The exact trigger, checks and timing are for the adviser to settle.

---

## PA-PAY-2026-12 · clause 1.4 (replaces PA-PAY-2026-11 clause 1.4)

**Current (2026-11):**
> 1.4 During the pilot, PlotArt quotes artworks priced up to EUR 9,999.99. It will not quote a purchase that would bring a
> buyer's apparently linked purchases through the pilot to EUR 10,000 or more in twelve months. Linked purchases are those by
> the same buyer, or by anyone PlotArt knows to be acting with them. These are limits on the scope of the pilot, not a
> statement about anyone's legal obligations.

**Variant 1:**
> 1.4 PlotArt quotes artworks at any price, up to the largest single card payment Stripe accepts. It will not quote a
> purchase that would bring a buyer's apparently linked purchases through PlotArt to EUR 10,000 or more in twelve months.
> Linked purchases are those by the same buyer, or by anyone PlotArt knows to be acting with them. These are limits on the
> scope of PlotArt's service, not a statement about anyone's legal obligations.

**Variant 2 (subject to advice):**
> 1.4 PlotArt quotes artworks at any price, up to the largest single card payment Stripe accepts. Before it quotes or
> completes a purchase, PlotArt may ask the buyer and the artist for the information and documents it needs to meet its
> legal obligations, including verifying the buyer's identity where a purchase, alone or together with purchases that are or
> appear to be linked to it, reaches EUR 10,000 or more. The artist will give PlotArt the information it reasonably asks for
> these checks. PlotArt may pause or decline a purchase it cannot lawfully complete; the buyer is then not charged.

## PA-BPT-2026-12 · clause 4.4 (replaces PA-BPT-2026-11 clause 4.4)

**Current (2026-11):**
> 4.4 During the pilot, PlotArt cannot arrange purchases of EUR 10,000 or more. This includes several purchases that together
> reach that amount.

**Variant 1:**
> 4.4 PlotArt cannot arrange purchases of EUR 10,000 or more. This includes several purchases that together reach that
> amount.

**Variant 2 (subject to advice):**
> 4.4 For a purchase of EUR 10,000 or more, alone or together with purchases that are or appear to be linked to it, PlotArt
> may need to verify your identity and ask you for information before your quote is issued. PlotArt may decline a purchase it
> cannot lawfully complete; you are then not charged.

## PA-BAA-2026-12 · clause 1.3 (replaces PA-BAA-2026-11 clause 1.3)

**Current (2026-11):**
> 1.3 Scope. The basket covers existing original artworks priced from EUR 1.00 to EUR 9,999.99, sold in euro, for delivery in
> the Republic of Ireland. It does not cover prints, commissions of new work, hire, discounts, gift cards or instalments.
> PlotArt will not accept a basket that would bring a buyer's apparently linked purchases through PlotArt to EUR 10,000 or
> more in twelve months (PA-PAY 1.4 applies). These are limits on the scope of the basket, not a statement about anyone's
> legal obligations.

**Variant 1:**
> 1.3 Scope. The basket covers existing original artworks at any price up to the largest single card payment Stripe accepts,
> sold in euro, for delivery in the Republic of Ireland. It does not cover prints, commissions of new work, hire, discounts,
> gift cards or instalments. PlotArt will not accept a basket that would bring a buyer's apparently linked purchases through
> PlotArt to EUR 10,000 or more in twelve months (PA-PAY 1.4 applies). These are limits on the scope of the basket, not a
> statement about anyone's legal obligations.

**Variant 2 (subject to advice):**
> 1.3 Scope. The basket covers existing original artworks at any price up to the largest single card payment Stripe accepts,
> sold in euro, for delivery in the Republic of Ireland. It does not cover prints, commissions of new work, hire, discounts,
> gift cards or instalments. PA-PAY 1.4 applies to the information and checks PlotArt may need before a purchase can be
> completed.

## PA-BBT-2026-12 · clause 3.3 (replaces PA-BBT-2026-11 clause 3.3)

**Current (2026-11):**
> 3.3 Limits. A basket can hold up to 10 artworks. PlotArt cannot arrange purchases of EUR 10,000 or more in total, including
> purchases that, together with other purchases by you or anyone PlotArt knows to be acting with you in the previous twelve
> months, reach that amount. An artwork priced at more than EUR 9,999.99 cannot be bought through the basket.

**Variant 1:**
> 3.3 Limits. A basket can hold up to 10 artworks. PlotArt cannot arrange purchases of EUR 10,000 or more in total, including
> purchases that, together with other purchases by you or anyone PlotArt knows to be acting with you in the previous twelve
> months, reach that amount.

**Variant 2 (subject to advice):**
> 3.3 Limits. A basket can hold up to 10 artworks. A purchase of EUR 10,000 or more in total, alone or together with
> purchases by you or anyone PlotArt knows to be acting with you, cannot be completed through the basket: PlotArt will
> instead contact you to complete the checks the law may require before it can be arranged. You are not charged for it
> through the basket.

*Drafting note on Variant 2 for the basket:* the basket takes the card and charges in one step, so identity checks cannot sit
inside it without new development. The simplest compliant route (to confirm with the adviser) is that baskets stay below the
threshold and larger purchases go through the existing quote from an enquiry, where checks can happen before the quote is
issued. That is what this wording describes.

## Other texts to review at the same time

- **Privacy Notice (V19):** Variant 2 means collecting identity documents and AML records (new categories, legal-obligation
  basis, retention set by AML law). V18 does not cover them.
- **PA-GAA / Founding Artist Agreements:** not changed by this. Commission terms are unaffected by price.
