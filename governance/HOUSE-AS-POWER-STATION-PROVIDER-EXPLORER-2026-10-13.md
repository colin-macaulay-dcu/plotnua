# House as Power Station — electricity-export Provider Explorer

**Date:** 13 October 2026 · **Discovery:** DISC-026 · **Page:** `discovery-house-as-power-station.html`
**Founder instruction:** "Resume the electricity-export Provider Explorer" (13 Oct 2026, after the Thermify / Zella DC / Tandem Compute research: Thermify stays international research, Zella DC parked, Tandem to GridNua B2B research, no residential computing opportunity approved for PlotNua).
**Status:** committed locally, NOT pushed. For founder review before publication.

## Value test — why this is not a duplicate

| Existing surface | What it says about suppliers |
|---|---|
| Discovery page, position 7 "Meter, export, tax" | Every supplier must pay for eligible export; rates are not regulated. Names no supplier. |
| Property Check (`disc026-power-station.html`) | "Ask your supplier…" in four places; "Export rates are set by suppliers and change — we will not print one." Names no supplier. |
| `supplier-export-evidence.json` (22 Sep pilot) | Machine-readable pilot, explicitly NOT homeowner-facing and NOT wired to the journey. Not a page. |

There is **no** published supplier comparison. The Explorer answers the question both surfaces stop at ("ask your supplier"): what four named suppliers actually say about who they pay, what meter and form they need, what happens without a smart meter, and how and how often the credit arrives. It shows **no rates and no earnings**, so it does not re-enter the rate comparison the pilot forbids.

## Evidence — re-read 13 October 2026

The 22 September pilot capture had **drifted** and was not used as the Explorer's evidence:

| Supplier | Pilot (22 Sep) | Official page (13 Oct) |
|---|---|---|
| Electric Ireland | deemed export: not publicly evidenced | "If you're not eligible to have a smart meter installed, then you'll be paid a deemed export calculation." |
| Bord Gáis Energy | customer requirement: not publicly evidenced | "You're an existing Bord Gáis Energy electricity customer, or you're signing up…" |
| Bord Gáis Energy | 4 times per year | page says both "4 times per year" and "every six months" — disclosed on the Explorer |
| Energia | customer requirement: not publicly evidenced | "No, not at the moment. To join the Microgeneration Scheme, your electricity import and export must be with the same supplier." |
| Flogas | eligibility, smart meter, deemed, customer: not publicly evidenced | all four published (content sits in collapsed sections the pilot capture missed) |

29 verbatim quotes, all matched word-for-word against the pages as served on 13 Oct 2026, are held in `atlas-tools/power-station-provider-sources-v1.json`. Capture hashes (sha256, first 16): Electric Ireland `914f27c30268b7ea` · Bord Gáis `fa90fff083cc6bee` · Energia `b2c78e7985c988f1` · Flogas `420b992d5f83b3f2`.

**Recommendation (not actioned):** regenerate `supplier-export-evidence.json` and refresh the four Atlas ORG-ESUP notes from this re-read, as a separate approved task. Neither was changed here.

## Organisations

Bord Gáis Energy (ORG-ESUP-BGE) · Electric Ireland (ORG-ESUP-EI) · Energia (ORG-ESUP-ENERGIA) · Flogas (ORG-ESUP-FLOGAS). Existing Atlas records read back read-only: Service Provider, no Products, no Partner records, no partner status. No Atlas record created or changed. The tab note states the list is not complete and that every supplier must pay for eligible export.

## Rules enforced by the builders

- `build-power-station-provider-universe.py` U1–U5, W1–W5: Atlas record and DISC-026 pilot membership; no products/partners; every sentence cites its own supplier's page **and** named verbatim quotes; no ranking vocabulary, links, emails, Airtable identifiers, money, rates, kWh, earnings or numerals (except "NC6"); 90-day refresh with build-stop on staleness (next review due **11 January 2027**).
- `build-power-station-provider-explorer.py` P1–P12: shared `provider-explorer.js` and `maker-explorer.css` unchanged at their existing pins; placement straight after "The energy anatomy of your property", ahead of the Property Check handoff, which is unchanged; single "not PlotNua partners" statement; rest of page byte-identical to HEAD except the explorer, its stylesheet link and the Thermify label; computing caveats guarded.
- `prove-power-station-provider-guards.py`: 18/18 breaks caught, controls pass, files byte-identical.

## Thermify correction

`Britain · proposed` → `Britain · limited trial`. Basis: Thermify's own site — HeatHub "currently on a trial basis", first residential HeatHub installed within UK Power Networks' SHIELD trial, further trial installations limited by that commitment, production and first home installations expected 2027. The card sits under "Operating now, outside Ireland"; nothing implies Irish availability. Its other text, including "Their open programme today is for ten organisations, not households", is unchanged.

## Not changed

Property Check and its calculations · Compute Readiness check · `supplier-export-evidence.json` · `disc026-evidence.json` · Atlas · Results and Compare · Borrowed Garden and Living in the Garden Explorers · shared Explorer files · other Discoveries · search index (passes `--check` unchanged).

## Addendum — final wording (founder approval, 13 October 2026, 19:19)

Explorer approved subject to two tab-note corrections, applied verbatim:

1. "Every electricity supplier must pay for eligible export." → "Under Ireland's Clean Export Guarantee, electricity suppliers are required to offer payment for eligible exported electricity, subject to the applicable rules." Checked against `disc026-evidence.json` record `supplier_must_pay_for_export` (CRU Microgeneration Q&A, CRU/202366, verified 14 Sep 2026) and the Clean Export Guarantee as named on Energia's and Flogas's pages (re-read 13 Oct 2026).
2. "Each pays only households that also buy their electricity from it." → "The four suppliers listed here require customers to purchase their electricity from them to receive export payments under their published arrangements." Checked against the four `customer` quotes in `atlas-tools/power-station-provider-sources-v1.json`.

Layout, supplier records, evidence rules and the journey unchanged.
