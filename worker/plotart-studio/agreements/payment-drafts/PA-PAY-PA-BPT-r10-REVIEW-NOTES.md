# PA-PAY r10 / PA-BPT r9 / Privacy V18: review notes (20 November 2026)

Internal. These are drafts for founder review: nothing is issued or published, and nothing is legally reviewed. The r9 notes still apply except as changed here.

## Changes

**PA-PAY r10**
- **New 0.4:** for a Gallery Artist the addendum is a **written variation under PA-GAA cl. 13**. This resolves the conflicts without re-issuing PA-GAA:
  - cl. 4.2 (collectors pay the artist directly), cl. 8 (reporting and invoicing) and cl. 9 (refunds) are modified for pilot orders only;
  - cl. 21.1 (entire agreement) already includes cl. 13 variations.
- **Founding Artists:** 0.4(b) states that PA-FAA is unchanged. Founding Enquiries stay commission-free and out of the pilot (0.2(a), 1.3(a)).
- **Brackets removed:**
  - 2.3 (s.107 note);
  - 3.2: the statement is the commission record, with a VAT invoice if PlotArt is VAT-registered;
  - 7.5 and 7.9: unverified descriptions of how Stripe recovers negative balances, replaced by "a matter between the artist and Stripe";
  - 7.5: notices by email;
  - 9.3 (F14);
  - 9.9: points to the named privacy section.
- **Fee figures:** fixed to Stripe's pricing "as published on {issue date}", to be re-checked at issue.
- **Footer:** corrected, and now names the operator correctly.

**PA-BPT r9**
- 1.2: bracket removed.
- **New 1.3(d):** commission transparency. The seller pays PlotArt a commission out of the price; it is not added to what the buyer pays.
- **New 1.3(e):** curatorial ordering, with no paid placement. This is the CCPC marketplace ranking information.
- 3.3: the purchase confirmation is **emailed** as the confirmation of the contract.
- 7.2: aligned with the CCPC short-term right to terminate:
  - 30 days, counted from installation where installed;
  - refund includes delivery, made to the same card;
  - repair or replacement may be chosen instead.
- 8.4: notices are emailed.
- 9.4: points to the named privacy section.

**Privacy V18:** `PRIVACY-NOTICE-V18-DRAFT.md`, with six exact changes to V17. It replaces the r1 pilot section draft.

**Website (PR branch `plotart/payment-pilot-launch-wording`):** sentences saying PlotArt "doesn't take payment" are replaced with wording that the artist is the seller.
- **Scope:** 127 pages, 6 builders or renderers and 2 proof strings, with the launch manifest re-pinned.
- **Timing:** the new wording is accurate both before and after launch, so it can be merged at any time.
- **Kept, because still accurate:**
  - Commissions and Art for Hire: new commissions and hire are excluded from the pilot;
  - Mobile Gallery host wording: addressed to galleries;
  - TRIQ.
- **Launch-only (published with V18, not before):** add to terms.html after "…is not acting as agent for either party.":
  > In the PlotArt payment pilot, PlotArt receives cancellation notices and complaints on the artist's behalf, and makes refunds on the artist's instruction, as the PlotArt buyer purchase terms explain.

## Consistency check (PA-GAA, PA-FAA, PA-PAY r10, PA-BPT r9, Privacy V18, website)

| Topic | Result |
|---|---|
| Seller | Artist is the seller everywhere (PA-GAA 4.2; PA-PAY 2.1; PA-BPT 1.1, 1.3; V18; website) ✔ |
| Stripe Connect | Payment into the artist's own Stripe account; no escrow (PA-PAY 2.4, 5.2; PA-BPT 3.1; V18) ✔ |
| Commission collection | Application fee for pilot orders; invoicing for all other sales (PA-PAY 0.4, 3.2; PA-GAA 8) ✔ |
| Commission rate and base | 15% of artwork only, VAT-inclusive, never on delivery (PA-GAA 5; PA-PAY 3.1) ✔ |
| Refunds and commission return | PA-PAY 7.7 is within PA-GAA 9 ✔ |
| Processing fees | PlotArt reimburses fee and VAT; shortfall by bank transfer within 30 days (PA-PAY 3.3–3.5; V18 bank details) ✔ |
| Delivery | Artist arranges delivery; transit insurance per shipment (PA-PAY 6; PA-BPT 5; website "arranges delivery") ✔ |
| Notices and confirmations | Emailed (PA-PAY 7.5; PA-BPT 3.3, 8.4; V18 email service) ✔. **Requires the live-email code change.** |
| Founding Artists | Commission-free enquiries untouched (PA-PAY 0.2, 0.4(b), 1.3) ✔ |
| Retention | PA-PAY 8.1 = PA-BPT 9.1 = V18 change 5 ✔ |
| Agency | PA-PAY 2.6 / PA-BPT 1.3(c) vs terms.html "not acting as agent": resolved by the launch-only sentence ✔ |

## Checked against official guidance (20 Nov 2026)

| Requirement | Source | Drafts |
|---|---|---|
| A marketplace must tell consumers whether the seller is a trader, based on the seller's declaration | Consumer Rights Act 2022 s.107 (irishstatutebook.ie) | PA-BPT 1.2 and quote page ✔ |
| A marketplace must tell consumers how it ranks results and how consumer-law obligations are shared with the seller | CCPC "Selling products" | 1.3(e) ranking; 1.3(a)–(c) shared obligations ✔ |
| Confirmation of a distance contract on a durable medium (for example email) | Consumer Rights Act 2022, Part 4 (formerly S.I. 484/2013, reg. 12) | PA-BPT 3.3 email ✔. **Blocker until live email is on.** |
| 30-day short-term right to terminate for faulty or non-conforming goods; refund including delivery to the same payment method; consumer may choose repair or replacement | CCPC; CRA 2022 s.24 | PA-BPT 7.2 ✔ |
| 14-day cancellation; return cost must be stated where goods can't normally be posted | Consumer cancellation rules; CCPC | PA-BPT 6; PA-PAY 7.2 ✔ |
| GDPR Art. 13: purposes, legal bases, recipients, transfers with safeguards, retention | DPC "Right to be informed"; DPC transfers guidance | V18 changes 2–5 ✔ |
| Resend transfer safeguards | Resend: certified under the EU-U.S. Data Privacy Framework; DPA includes EU SCCs | V18 change 3 ✔ |
| VAT registration: services threshold €42,500 (from 1 Jan 2025) | Revenue (via Chartered Accountants Ireland) | Pilot commission is far below it on its own. PA-PAY 3.2 covers both cases. **Total PlotNua service income must be checked.** |
| DSA trader traceability (Art. 30) | CCPC DSA page; DSA Art. 29: does not apply to micro or small enterprises | PlotNua is a micro enterprise, so expected **not to apply**. Seller information is collected anyway. |

## Unresolved without professional advice (accepted risks for a one-artist pilot; none confirmed)
1. Whether PlotArt is an "online marketplace" under s.107, or could be treated as seller or agent. The drafts are written to meet the marketplace duties either way.
2. Reliance on the artist's trader declaration. CRA s.107 bases the disclosure on the declaration, but liability if the declaration is wrong is untested.
3. VAT treatment of the fee reimbursement (reduction of commission or separate payment), and whether PlotNua must register once all its service income is counted.
4. AML status as an art intermediary. The €9,999.99 cap and linked-purchase check limit exposure; they are not compliance.
5. Payment-services regulation. PlotArt never holds buyer funds (direct charges), which is the standard Stripe Connect model, but this is not confirmed.
6. DAC7 platform reporting.

## Remaining blockers before a live payment
1. Founder approval of these texts, then issue: fingerprinted HTML, migration 0018 and artist acceptance.
2. V18 and the terms.html sentence published with the launch.
3. A code change to enable live mode and live email. Both are refused by design today.
4. Production migration and deployment; live Stripe activation and the artist's live onboarding.
5. Transit insurance confirmed for the first shipment; a funded Stripe platform float.
