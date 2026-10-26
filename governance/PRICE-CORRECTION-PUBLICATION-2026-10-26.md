# Approved price correction publication — 26 October 2026

Founder approved the reviewed 59-record correction package and publication of the catalogue and shared aggregate correction. This is a scoped correction to the existing research snapshot, not a full market refresh.

## Verified catalogue release

PR #6 deployed commit `310f45366eb7a6635ee0af0ec4b13724f83bf9af`.
Universe SHA-256: `7f70a52b0650966f929bee3d54f91be6a5f42f2d63bd69b25182024109c8f0ba`.

All PR and post-merge checks, including Pages, passed. Live HTTP 200 catalogue, detail evidence and Search responses matched the release bytes. Exactly 59 approved price/base-price and last-check-date changes were confirmed; 47 prices increased and 12 decreased. All non-target products, VAT treatment, price scope, eligibility and imagery were preserved. The Shomera Search entry and all Search counts were preserved.

## Shared evidence correction

The existing correction register names the actual verified deployed commit above. The cost generator reproduces the original evidence byte for byte before applying the prior five-record correction and this additional 59-record correction. The original 7 October snapshot identity remains visible.

The only changed displayed price boundary is the unspecified-scope range minimum: €4,713 to €4,789. Its maximum remains €43,450. The other displayed ranges remain €9,995–€43,650 and €3,624–€23,990. Product/supplier counts and VAT/classification totals remain unchanged. Both pages disclose the additional correction; the pricing methodology's latest check date becomes 26 October.

## Design preservation and maintenance

The legacy main-page layout builder correctly refuses writing to the approved Premium page. That lock is unchanged. `refresh-garden-cost-figures.py` maintains only the existing evidence list using the shared pure figure renderer. It requires exactly one matching old list or one already-current list, refuses ambiguous input and preserves all bytes outside the list. It does not run the legacy layout builder's writing modes.

The P2 claim guard now traces a correction record count to its enumerated verified product array rather than treating it as an untraced integer. No number is hard-coded into the allowance. A deliberately incorrect count is refused.

The freshness workflow now also verifies the deployed correction chain, the main-page evidence list and all 18 main-page claim guards. The frozen extract and pricing-page checks continue unchanged. No new permission scope is added.

## Validation and limits

Local evidence reproduction, frozen extract reproduction, pricing-page checks, bounded updater checks, all 18 main-page claim guards, Premium pricing preservation and all legacy Premium locks pass. The generated ranges and counts match the approved review package. Duplicate, missing and mixed evidence regions are refused; idempotence is confirmed. A wrong correction count is rejected by P2.

The oldest price in a published range is still checked on 8 August. Whole-guide freshness remains through 6 November; first refusal remains 7 November. Garden Office Solutions' disputed prices, founder-held groups and excluded undated prices remain unchanged. No additional Airtable writes, analytics changes, planning edits or outreach form part of these releases.

Production verification of the aggregate release will be recorded in its pull request after deployment; this document does not anticipate that outcome or claim a Google ranking change.
