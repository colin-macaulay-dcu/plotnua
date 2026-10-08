# PlotNua Search V1 — Freeze / Release Record

**Status:** CLOSED — live, verified, frozen
**Release commit:** `8105b52d35c05501f8b522b4802fb945b8db6302`
**Parent:** `1bf7d4b` (Powersheds correction freeze record)
**Released:** 2026-10-08
**Founder:** Colin MacAulay
**Governing contract:** [`SEARCH-V1-CONTRACT.md`](SEARCH-V1-CONTRACT.md)

This record closes Search V1. It states what shipped, what was proven, and what
was deliberately left open. It is a record of verification, not a summary of
intent — every figure below was measured against the live production origin or
the committed tree, not carried forward from the build.

---

## 1 · Acceptance

| Gate | Result |
|---|---|
| Founder real-browser acceptance | **PASS** |
| Production deployment | **PASS** |
| Deployed files byte-identical to `8105b52` | **PASS** |
| Production discrepancies found | **NONE** |

Founder acceptance was given after four rounds of real-browser review. Each
round found genuine defects that the automated suites had not caught — the
Eircode flash, the wrong back-label, and the Back-to-homepage failure were all
found by a person using the product, not by a test. That is recorded here
because it is the most useful thing this release has to teach: the suites were
necessary and were not sufficient.

---

## 2 · Deployed artefacts, verified byte-identical

Hashes read from `https://plotnua.ie` and compared against the committed tree at
`8105b52`. SHA-256, first 16 hex characters.

| File | SHA-256 (16) |
|---|---|
| `search.js` | `a85193e7dd6982f1` |
| `search.css` | `a0a1b07aaf6f729a` |
| `search-index-v1.json` | `98efc7e85f796ba8` |
| `search.html` | `a8dd597348413835` |
| `index.html` | `72b5cbb522305ed6` |
| `your-plot.html` | `8ef531bfb5ed5b37` |
| `sitemap.xml` | `4eb6ccb1ece3a591` |
| `discoveries.html` | `d88f623647f4ddb2` |

All returned HTTP 200 with correct content types. The approved Search pill
markup hashes to `033652069264d4c4a89f330c90fcc1a2eecc43d8f3070a35ff73151865ab988b`
on every faded page, and to the `nofade` variant — differing by exactly one
attribute, `data-pns-nofade="true"` — on the two pages whose brand mark has no
fade mechanism (`discoveries.html`, `search.html`). 19 faded + 2 nofade = the 21
public surfaces. Both variants are pinned by assertion; neither is a deviation.

---

## 3 · The live journey, verified end to end

Homepage → **Search PlotNua** → `Powersheds` → supplier expansion →
**12x12 Apex Classic Log Cabin** → Product Detail → **← Back to Search** →
query, results and expansion restored.

Every step was performed against production, not a local build.

**Powersheds search result:** exactly **1 supplier + 3 products** (4 results).
The supplier row reads `3 products in Atlas · from €6,129` and expands in place
to its three products. The supplier name is deliberately not a link and does not
look like one, because a supplier has no route to navigate to.

**Governed product price verified: €6,129 – €6,219.** This matches the governed
record exactly — `priceEvidence.from = 6129`, `priceEvidence.to = 6219`,
`status = Verified`, adjudicated from a single price record
(`recfb1UXi3nW7ekH4`, last checked 2026-09-28). Search itself carries only the
floor, `6129`, which is what produces the `from €6,129` on the supplier row.
Search did not invent, round, widen or re-derive a price.

**No Eircode flash.** Measured at the moment Product Detail opened:
`#screen-entry` was `opacity: 0, visibility: hidden`, no Eircode text present in
the document, and the pre-paint hold class had been released cleanly. The
original defect was that `#screen-entry` ships without `.is-hidden` and is
therefore visible in the first paint, before any deferred script runs; the fix
is a classic pre-paint script plus CSS suppression, which is the only hook that
exists before first paint.

**Back control reads `← Back to Search`** for a Search-origin homeowner, and
returns to Search with the query, the four results and the supplier expansion
all restored.

---

## 4 · Privacy, verified in production

- **The search term is absent from the URL.** After the full journey the address
  is `https://plotnua.ie/` with no query string and no fragment. The product
  deep link carries only `?product=<governed-record-id>&from=search` — a stable
  Airtable record id, never a product name and never the search term.
- **The search term is absent from persistent storage.** localStorage holds only
  the pre-existing `plotnua.myplot.v1`; sessionStorage is empty; the only cookie
  is the Cookiebot consent record. No storage value matches the query.
- **Restoration uses history state, not storage.** The query, results and
  expansion survive the return because they travel in a per-entry history state
  object, which is session memory and is never written to disk, never sent to a
  server and never readable by another page. `pushState`/`replaceState` are
  called with no url argument, so no address is ever written.

A note on why this is stated so precisely: the Back-to-homepage failure was
caused by the opposite mistake. The original guards banned the History API
outright, which forced the overlay to create no history entry at all, which is
what sent Back past Search to the homepage. The guards were re-specified to
assert that no state call passes a url argument — the real invariant — rather
than banning the mechanism that makes correct behaviour possible.

---

## 5 · Private-preview containment, verified

Searching for a supplier that exists only as a private preview returns an honest
empty result and nothing else. Verified live for **Capsule Castle, Honka,
Superior Pergola, Irish Sauna Company**, and the bare term **`preview`**. Each
returns *"We have nothing on <term> yet"* with a single link to
`discoveries.html`. No preview URL is exposed, in any form.

**A false positive worth recording.** A leak scan flagged Hutsmith, Cosy Cabins,
Koto, Iglucraft and Yardbox as appearing in the index. They are *published*
Atlas suppliers that also happen to have private previews. Every one of their
index records carries `route: null`, and no route value anywhere in the index
mentions a preview. The complete set of route values is the governed product
template `your-plot.html?product={id}` plus sitemap-listed Discovery pages —
nothing else. The scan was matching supplier *names*, not routes. Containment
holds; the earlier alarm was the instrument's fault, not the product's.

---

## 6 · The governed corpus

| | Count |
|---|---|
| Products | **573** |
| Suppliers | **64** |
| Possibilities | **13** |
| Journeys | **9** |

Index size **137.5 KB** (140,815 bytes). `sourceUniverseSha256` resolves to
`garden-room-recommendation-universe-v1.json`, the governed universe.

**180 KB is a performance guard, not a corpus ceiling.** If the complete
governed corpus ever exceeds it, the build **fails** and the architecture is
reconsidered. The corpus is never silently reduced to fit. This was tested in
anger: the first build measured 180.9 KB and the guard fired. The response was
architectural, not editorial — the route template moved into the envelope
(−28.5 KB) and supplier `productIds` became runtime-derived (−14 KB), reaching
137.5 KB with **zero records dropped**.

---

## 7 · Final gates

| Suite | Result |
|---|---|
| Acceptance (`prove-search-acceptance.mjs`) | **148 passed, 0 failed** |
| Guard capability (`prove-search-guards.py`) | **19 capable, 0 blind** |
| Index guards (`build-search-index.py`) | **13 passed** |
| Rail guards (`build-search-rail.py`) | **10 passed** |

Every guard is demonstrated *capable of failing* against the current artefacts.
"It fired during development" was not accepted as capability proof at any point.
Catch-all guards run last so that specific diagnosis wins and each specific
guard stays independently fireable rather than masked.

---

## 8 · Deliberate non-changes

- **G5 switches unchanged and off.** `WRITES_ENABLED = "false"` and
  `EMAIL_ENABLED = "false"` in `worker/garden-register/wrangler.toml`, which is
  byte-identical to HEAD. `INTEREST_PUBLIC = false` in
  `disc025-borrowed-garden-check.html`, also byte-identical. No G5 work was done.
- **Powersheds source data unchanged** since `a3a1b80`. Three products, no
  legacy "Power Sheds" spelling anywhere in the universe.
- **P12_no_new_css** remains recorded OUT OF SCOPE and open, as a pre-existing
  stale cross-build guard. Not repaired, not suppressed.
- **The left-hand controls were not touched.** An earlier design put Search into
  the left rail as MARK → SEARCH → INFO; founder review rejected it and it was
  reverted in full. `search.css` declares no rule whose subject is `.brand-mark`,
  `.brand-info` or `.brand-info-pop`. Search moved out of their way rather than
  making them move.

---

## 9 · Parked tooling defects — OUTSIDE Search V1 closure

Both were found during release verification. Both are real. **Neither is
repaired in this record, and neither affects the released product.**

**TOOL-1 · `build-search-rail.py --verify` is not read-only.**
It rewrites all 21 governed pages. Because the injection is idempotent (guard
R10), the rewrite produced byte-identical output and nothing drifted — verified
against the frozen hashes. But a flag named `--verify` that writes is a trap: a
future operator will reasonably believe it is safe to run against a clean tree.

**TOOL-2 · `build-search-index.py --verify` is not read-only.**
It regenerates `search-index-v1.json`, changing the `generated` timestamp and
`sourceCommit` metadata. This was caught during verification when the rewritten
file hashed to `4379d452f517197b` against the deployed `98efc7e85f796ba8`. The
573 records were confirmed **byte-identical**; only the two metadata fields
differed. The file was restored from `8105b52` and the tree re-proved clean
before this record was written.

Both are explicitly outside Search V1 closure and are not to be repaired as part
of it.

---

## 10 · Closure

Search V1 is **LIVE, VERIFIED and FROZEN** at
`8105b52d35c05501f8b522b4802fb945b8db6302`.

No production discrepancy was found. The released artefacts are unchanged by the
writing of this record.
