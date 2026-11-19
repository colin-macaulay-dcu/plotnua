# PlotArt checkout decisions, 19 November 2026

Buyers should be able to buy available works from multiple participating artists in one basket and one payment. Each artist can fulfil their own part of the order. The shop should adopt PlotArt's existing visual identity. Test checkout and artist allocations before a production release.

Keep the agreement and direct-payment process already accepted by each existing artist. There is no immediate request to contact or re-sign existing artists. Preserve Founding Artist commission-free entitlements, including qualifying enquiries. The proposed first managed-checkout cohort is new Gallery Artists on the 15% agreement who expressly opt in. Keep the founding route available under its existing terms. Draft and version any future payment terms before offering them online. Record who accepted which terms and when.

Before live payments, settle responsibility for processing fees, refunds and disputes, the commission basis, payout timing and artist fulfilment. A preference to avoid solicitor costs is a budget decision, not a legal determination.

Run 44 recognised the test credential and stopped before payment because both test accounts lacked the Accounts v2 recipient transfer capability. The next sandbox proof requests that capability on both fixtures, checks readiness, and exercises one €10 payment, €6 and €4 allocations, and a €6 partial refund and transfer reversal. These figures are synthetic.

Run 46, attempt 2 passed all six checks. Stripe confirmed one €10 sandbox payment, transfers of €6 and €4, a €6 buyer refund and reversal of the first transfer. The second recipient retained €4. This verifies the provider transactions. A buyer completing the same order from the PlotArt basket remains to be verified. [GitHub job](https://github.com/colin-macaulay-dcu/plotnua/actions/runs/44491972557/job/135453682472)

Run 51 passed the buyer browser test. One hosted Stripe sandbox checkout for Rowan Studio and Alder Studio returned to a server-verified PlotArt receipt for €3,585 with Irish delivery and studio collection. Run 46 separately verified artist transfers and a partial refund. The hosted checkout implementation sets a transfer group but does not yet create the artist transfers for this purchase. [Run 51 evidence](https://github.com/colin-macaulay-dcu/plotnua/actions/runs/44501598660/job/135482521586)

Run 52 passed the integrated sandbox test. One €3,585 hosted checkout produced one combined buyer confirmation and two automatic gross transfers (€1,485 to Rowan including €35 delivery, €2,100 to Alder for collection). Replaying the signed payment notification returned the same two transfers. Commission deductions and real bank payouts were outside this test. [Run 52 evidence](https://github.com/colin-macaulay-dcu/plotnua/actions/runs/44503909832/job/135490417588)
