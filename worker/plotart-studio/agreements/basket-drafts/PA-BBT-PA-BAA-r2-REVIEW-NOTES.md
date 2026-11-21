# PA-BBT-2026-11 and PA-BAA-2026-11 — r2 review notes (22 November 2026)

Not part of either text. No solicitor-review stage (founder decision, 22 Nov 2026). This file records the consistency review against the issued agreements and the code, and the few legal risks that remain genuinely open.

## A. Founder decisions applied

- Founding 25: 0% PlotArt commission during the agreed commission-free period; the artist bears Stripe's actual processing fees only with explicit, separate, revocable opt-in consent (PA-BAA 3.4, 4). In code: `BASKET_DECISIONS.commission_free_lines_live = 'with_processing_consent'`, consent recorded in `basket_consents` (migration 0020).
- Gallery Artists: 15% (PA-GAA 5), PlotArt reimburses Stripe's processing fee, combined deduction never above commission. No commission on delivery. No buyer fees.
- Participation optional; declining changes nothing for gallery listing, enquiries or direct sales. PA-FAA, PA-GAA, PA-GPIL, PA-PAY and PA-BPT unchanged.

## B. Inconsistencies found and corrected in r2

| Was (r1) | Problem | Now (r2) |
|---|---|---|
| PA-BBT 7.2 / PA-BAA 2.3(b): 14 days from the last artwork in the whole basket; PlotArt to tell artists the last delivery date | Not implemented; extended each artist's exposure because of other artists' deliveries | 14 days from receipt; for several works from the **same seller** delivered separately, from the last of them (CRA 2022 / CRD art. 9(2)(b)) |
| PA-BBT 6.1: basket page states packer, carrier and insurer | The basket page shows charge, window, tracking, "insured" and return cost; the full detail is in the confirmation | Says exactly what is shown before payment and what the confirmation adds |
| PA-BBT 3.1(d): "select Checkout" | Did not say which click places the order | Confirming on Stripe's page places the order with an obligation to pay; Stripe's page now shows "By confirming, you order the artworks in your basket and agree to pay €X in total." |
| PA-BAA 2.2: seller details shown on the basket page | Basket page is open to anyone; a home address could be exposed without the artist's informed choice | Separate recorded confirmation, bound to the exact information; withdrawn automatically if it changes |
| PA-BAA 4.5: short consent wording | Did not cover refunds, disputes, gallery/enquiries | Replaced with the exact statement the code records (also C2 test) |
| PA-BAA 4.1: consent recording | Did not say what is recorded | Artist, account, addendum version and fingerprint, statement, time, given/withdrawn, mode |
| PA-BAA 12.1 | Onboarding wording | Adds seller-information confirmation and payouts enabled (both enforced in code) |

Checked and consistent: amounts and limits (10 works, €9,999.99, €10,000 linked over 12 months), hold times (31 + 15 min; +30 min for bank confirmation), delivery region (ROI), per-artwork charges, all-or-nothing authorisation, refunds/pending/reversed refunds (PA-PAY 7.5–7.6), records (PA-PAY 8), data shared (PA-PAY 9), fresh live acceptance (PA-PAY 10).

## C. Genuinely open legal risks (only these)

1. **Order button wording (CRA 2022 / CRD art. 8(2)).** The final click is on Stripe's hosted page in setup mode, whose button label Stripe sets. We add explicit order wording beside it (custom text). If Stripe's label is not an "order with obligation to pay" equivalent, a consumer could argue they were not bound. Check the live label on the first TEST run; if weak, the fallback is to label our own button "Buy now" and state the total there.
2. **Seller address of home-based artists.** The law requires the geographical address where the trader is established; a home-based artist may only have their home. Handled by the artist's explicit confirmation (they can decline and keep selling directly); not otherwise resolvable.
3. **Privacy notice V18 not yet published.** PA-BPT 9.4 and PA-BBT 10.4 refer to it. Publish V18 with `PRIVACY-NOTICE-V18-BASKET-ADDITION.md` at launch.

Not treated as open: Founding fee consent vs PA-FAA cl. 3/13.2 (optional, revocable, Stripe's own fee, PlotArt takes nothing); €10k cap (operational pilot limit, as issued); VAT (unchanged from PA-PAY 3.6/3.9).
