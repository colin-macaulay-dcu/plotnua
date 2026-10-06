# PHASE 6B · RELEASE DIFF AND LIVE DECISION
**6 October 2026. NOT APPLIED. Nothing staged, committed, pushed or published.**

## VERDICT: **NO-GO** for live five-band integration.
Section B could not be satisfied. The candidate that would justify the bands has never been
generated from live Atlas in this session, so Section C's production gate has never run on a real
production artefact. Everything below is measured against a **labelled projection**, not that candidate.

---

## THE BLOCKER (Section B)
`generate_garden_room_universe.py` reads live Atlas **only** via `AIRTABLE_TOKEN` from the
environment. In this session:

```
AIRTABLE_TOKEN: NOT SET
::error:: AIRTABLE_TOKEN is not set. This script reads it from the environment
          only, and never accepts a credential by any other route.
          Nothing was written.
```

No `.env`, `.envrc` or secret file exists in the workspace; nothing in the environment matches
`airtable`. The only other input is `--snapshot`, a raw six-table Airtable dump. Assembling one
through the Airtable MCP would mean paging **1,199 products + 8,224 feature values** plus four more
tables through this conversation and then certifying its faithfulness with my own tools — weaker
provenance than the real read, and exactly the self-certification this project avoids. Not done.

### THE UNBLOCK — no code change required
`.github/workflows/atlas-match-qualification-dry-run.yml` already does precisely this run:
`workflow_dispatch`, `AIRTABLE_TOKEN: ${{ secrets.AIRTABLE_TOKEN }}`, read-only, output to
`RUNNER_TEMP` outside the tree, verifies the repo was not modified, uploads the artefacts.

**Run it from the Actions tab.** Optionally add `--write-snapshot` so the raw read is replayable.
Then Phase 6B Sections C–G can be re-run against the genuine artefact.

---

## WHAT WAS VERIFIED (Section A) — no writes
All 16 release-critical Product Pricing records re-read from live Atlas and matched to the Phase 6A
ledger exactly: 2 created Garden Rooms range records, 2 Shomera, 1 Big Man (cleared + Archived),
8 Loghouse, 3 Power Sheds (untouched).

Incidental observation, no action taken: the three Power Sheds records carry Price Type
`"    Standard Price"` — a **separate select option with four leading spaces**, distinct from
`"Standard Price"` used elsewhere. Pre-existing; harmless to the price pipeline; worth tidying in a
future authorised pass.

---

## H · THE EXACT BOUNDED DIFF THAT WOULD BE REQUIRED

### 1 · `your-plot.html` — one constant, one behaviour
`AS_BUDGET_BANDS` at **line 15658**. Referenced at lines 9883 (comment), 16517 (comment),
**17151 (×2 — the live band lookup)**, 17494 (comment), 22704, 22727, 25364, 25398.

```js
// FROM (four bands, open top)
const AS_BUDGET_BANDS = {
  'under-10k': { lo: 0, hi: 10000 }, '10k-20k': { lo: 10000, hi: 20000 },
  '20k-30k': { lo: 20000, hi: 30000 }, '30k-plus': { lo: 30000, hi: Infinity },
};

// TO (five bands)
const AS_BUDGET_BANDS = {
  'under-10k': { lo: 0, hi: 10000 }, '10k-20k': { lo: 10000, hi: 20000 },
  '20k-30k': { lo: 20000, hi: 30000 },
  '30k-50k':  { lo: 30000, hi: 50000 },      // NEW
  '50k-plus': { lo: 50000, hi: Infinity },   // NEW — replaces '30k-plus'
};
```

- **four-band → five-band map:** `under-10k`→`under-10k`, `10k-20k`→`10k-20k`, `20k-30k`→`20k-30k`,
  **`30k-plus` splits into `30k-50k` + `50k-plus`**.
- **retired key:** `30k-plus`. Any persisted My Plot answer holding it must migrate — a saved
  `30k-plus` becomes `30k-50k` when the stored budget is under €50,000, else `50k-plus`. Without
  this, `AS_BUDGET_BANDS['30k-plus']` returns `undefined` and ranking silently drops the budget axis
  (the existing comment at line 9883 documents that exact failure mode).
- **budgetFit safety behaviour:** `shadowBudgetFit` returns `2` only when the price is in band **and**
  `priceSafeForMatching === true`; `1` when in band but unsafe/conflicted; `0` out of band. Only `2`
  may be presented as a budget match. This is what suppresses 11 unsafe EUR rows.
- **homeowner price/basis line:** price plus a plain-English basis from `priceBasisClass`
  ("Installed, with electrics" / "Collection from the maker" / "Check what's included"), and a VAT
  clause only from `vatStatus` — never inferred.
- **From behaviour:** `priceIsRangeFloor === true` renders "From €X". 90 of 477 rows qualify.
- **VAT behaviour:** `vatStatus` ∈ Yes/No/Unknown drives the clause; `Unknown` prints no VAT claim.
  `vatRate` stays `null` — no VAT Rate field in this phase.

### 2 · Generator — widen the export, change no price logic
The operative universe carries `priceBasis` but **none** of the 13 fields the bands need. Add to the
product export: `priceRecordIds`, `priceRecordIdsAvailable`, `priceStatus`, `priceType`,
`priceScope`, `vatStatus`, `vatRate`, `priceBasisAxes`, `priceBasisClass`, `priceBasisConfidence`,
`priceIsRangeFloor`, `priceSafeForMatching`, `priceEvidenceRef`. Retain `priceBasis` for
compatibility. No change to `adjudicate_price()` or `price_record_number()`.

### 3 · Operative recommendation universe
`garden-room-recommendation-universe-v1.json` (sha `7a3e7db8…`) replaced **wholesale** by the
CI-generated candidate — never hand-edited, never patched. Atomic swap, last-known-good retained,
exactly as `atlas-match-universe-refresh.yml` already does.

### 4–5 · The two JSON consumers — **NO CHANGE REQUIRED**
`garden-room-detail-typicalhomeowner-v1.json` and `garden-room-detail-evidence-v1.json` each contain
exactly one occurrence of `10k-20k`, and it is **curator prose, not a band key**:

> `/products/rec280lNwFUpajNBI/typicalHomeowner/text` — "An Irish homeowner working to roughly
> EUR 10k-20k who wants a durable, low-upkeep room…"

Neither file holds `under-10k`, `20k-30k` or `30k-plus`. **A repo-wide find-and-replace of band keys
would corrupt this sentence.** Both files must be left alone.

---

## KNOWN EXCLUDED DEFECTS
1. **Live-Atlas generator bridge** — blocks B, C and therefore the release.
2. **Ecohouse unpriced** — the 7 proposed figures were not verified and are locked out. Today's site
   publishes ranges inc. VAT (6×4m €27,090–€36,420, 5×4m €23,190–€31,590, 6×3m €22,840–€31,240).
   Needs a separate authorisation.
3. **17 pre-existing ambiguous products** — DREUX ×4, Duraboard ×6, MCD ×4, LILLE, WISSOUS, Garden
   Office Ryan 1. Duplicate equal-authority Verified records hit `adjudicate_price()` rule 4.
   Identical set in Phase 5 and the projection; Phase 6A introduced none.
4. **€50k+ overshoot, not fixed** — open-ended band, 9 products / 3 suppliers, €54,950–€149,900.
   A €60,000 homeowner can still be shown €149,900: **2.5×**.
5. **Structured `vatRate`** — no field exists; 13.5% remains prose. Locked for this phase.
6. **ULTIMATE 27** — €51,000 ex-VAT, no published inclusive total, not a governed price.
7. **334 inherited curator-prose markers**; **PRODUCT EQUIVALENCE** (Ecohouse/Loghouse shared
   products) deferred; **Power Sheds whitespace select option**.
