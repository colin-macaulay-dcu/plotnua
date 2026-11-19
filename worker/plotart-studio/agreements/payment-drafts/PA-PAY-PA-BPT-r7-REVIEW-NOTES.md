# PA-PAY / PA-BPT r7: internal review notes (17 November 2026)

**Internal. Not customer-facing. Neither draft is issued, accepted or installed.** These notes add to the r6 notes; they do not replace them.

## 1. Changes from r6 to r7, and what they rest on

| # | Area | PA-PAY r7 | PA-BPT r7 | Behaviour it rests on (code, run 20) |
|---|---|---|---|---|
| 1 | Seller information | Cl. 2.2: the artist enters it in Studio and confirms it. A quote cannot be approved or issued without it. Each quote keeps its own copy. If the information changes after approval, the quote must be approved again. | S.1.1 unchanged; it is filled from the quote snapshot. | `seller_profiles`, `sellerProblems`, `profileHash`; local checks SP1–SP6, QS1–QS3 |
| 2 | Trader status (F2) | Cl. 2.2 bracket: traders only by default, with the alternative stated. | S.1.2 drafting note updated. | `CHECKOUT_ALLOW_NON_TRADER_SELLERS` unset means only traders are quoted (local check SP5). |
| 3 | Returns | Cl. 7.2 unchanged in substance. It is now enforced: method, address, cost (fixed or estimated maximum), and who arranges the return. | S.6.3 unchanged. | Delivery fields `return_*` and `returnProblems` (local checks RT1–RT2); shown on the buyer page and in the confirmation. |
| 4 | Buyer confirmation | Not covered. | New s.3.3: the confirmation's contents. The buyer can open it from the quote link and PlotArt keeps an exact copy. Email sending is bracketed until before live payments. | `order_messages` and `order_message_deliveries`, test sink only (local checks BC1–BC6; real E15). |
| 5 | Pending refunds | Cl. 7.5: "A pending refund has not been completed: the buyer has not been repaid until Stripe completes it." Telling the buyer is bracketed until buyer notifications exist. | S.8.2 now uses the same sentence. S.8.4 is bracketed. | Buyer notifications for refunds do not exist yet (gap G3). |
| 6 | Example 2 | Now described as an agreed partial refund of the price of the one original artwork, which the buyer keeps. | — | — |
| 7 | Deadlines | Cl. 3.3(b) [7 days] and 3.5 [30 days] are marked provisional, awaiting founder approval. | — | `deadlines()`. The queue shows "provisional" until `CHECKOUT_DEADLINES_APPROVED` is set (local check OQ1; MB8b). |
| 8 | Lost disputes | Cl. 7.7(c): Stripe's notice that the dispute was lost counts as notice under PA-GAA 9.1, and commission is returned within 30 days. | — | `lost_dispute_commission` queue item, due in 30 days, not provisional (local checks LD1–LD3; real E16). |
| 9 | Statements | Cl. 3.8 rewritten as a list. Owed and paid amounts are separate. Dispute fees appear as Stripe records them. If Stripe has not supplied a fee, the statement says so. | — | `statement()` (local checks DF1–DF2; real E14 and E16 statements). |
| 10 | Bank details | Cl. 3.5: bank details are asked for by phone and not kept. Cl. 9.7 is aligned with this. | — | The pilot refuses references that look like bank details (local check OQ2). Procedure in `PILOT-SHORTFALL-PAYMENTS.md`. |
| 11 | Retention | Cl. 8.1: the records include the quote snapshot, the confirmation and the owed/paid records. Nothing is deleted while a dispute is open. A late dispute places a hold automatically. Seller information is deleted when the artist leaves. | S.9.1: never deleted while a dispute is open; the record includes the quote and the confirmation. | Sweep guard, database trigger, automatic hold (local checks RH1–RH3). |
| 12 | Privacy | Cl. 9.2–9.5 rewritten from the access check (section 3 below). | S.9.2(c) rewritten from the same check. | Run 20, V1–V5 |

## 2. Founder decisions

| # | Decision | Status |
|---|---|---|
| F2 | Traders only | Open. The code defaults to traders only. |
| F5, F6, F7, F8, F9, F10 | See r5 and r6 notes | Open. F6 (commission after a lost dispute) now has a queue item and button; it is not automatic. |
| F11 | Shortfall payment period (30 days) | **Open, provisional** |
| F12 | Reimbursement period (7 days) | **Open, provisional** |
| F13 | Add-on fee exclusion list | Open |
| F14 | **New:** whether to ask Stripe for narrower access, because PlotArt's key can view artist identity and bank details it does not need (section 3). | Open |
| F15 | **New:** who monitors the "amounts owed" queue, and how often. | Open |

## 3. Privacy access check (run 20, test mode; field names only, no values recorded)

| Data subject | What PlotArt's key **can view** at Stripe | What PlotArt **stores** |
|---|---|---|
| Artist (v1 account) | email; business mcc, support phone and URL; individual name, email, address and date of birth; bank name, country, routing (branch) number, last 4 and fingerprint. **Not** the full account number. | Account status and the names of outstanding requirements |
| Artist (v2 with `include=identity`; the pilot does not request this, but the key can) | identity: address, date of birth, documents, `id_numbers`, phone, given name and surname | Nothing |
| Buyer (Checkout Session) | name, email, address (country only) | Email (given by PlotArt with the quote) |
| Buyer (charge) | card brand, country, funding type, expiry month and year, last 4, fingerprint and network details; billing address; receipt URL. **Not** the full card number. | Nothing beyond payment ids and amounts |

**Assessment.** Access is broader than the pilot needs, in particular artist date of birth, identity numbers and bank branch details. PlotArt does not copy these, and the drafts now say so. Narrowing the key's permissions is for the founder to decide (F14); nothing has been changed.

**Privacy notice: changes needed** (in addition to section 6 of the r5 notes):
- the "can view but does not store" list above;
- seller information is shown to buyers;
- quote snapshots and purchase confirmations are kept;
- the test mail sink;
- amounts-owed records, which hold no bank details;
- bank details obtained by phone only when PlotArt must pay an artist directly, and not kept in PlotArt's systems.

## 4. Gaps remaining

**Necessary before live use**

| # | Gap |
|---|---|
| G1 | **No email provider.** Confirmations and notices go to the test sink only. Live sending needs a provider, a sending domain and approval (F9/F10). |
| G2 | **Fully unfunded refund.** The second account (`acct_1Uct3vHx1OnYJa8H`) is created. Waiting for founder onboarding, then the test, then finalising PA-PAY 7.5. |
| G3 | **No buyer notices** for pending, failed or reversed refunds (drafts bracket them). |
| G4 | Approval of the provisional deadlines (F11, F12) and a monitoring owner (F15). |
| G5 | The r5 and r6 open items that remain: live pricing and VAT; the countered dispute fee (not charged in the sandbox); the professional-review points. |

**Optional**
- An online cancellation form with automatic acknowledgement.
- Placing the dispute-fee record automatically on the founder's monthly report.
- Narrower Stripe access (F14).
