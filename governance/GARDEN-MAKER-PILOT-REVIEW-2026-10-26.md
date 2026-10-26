# Garden maker editorial pilot: review

Status: two completed review drafts; publication not yet approved.
Base: `ce17c813efa2705ee46868e0e2c2a0c14e0ad16a`.

## Pages prepared

| Page | What it helps a homeowner decide |
| --- | --- |
| `concept-modular-garden-offices.html` | Whether to furnish an office themselves or choose a fitted interior, and what remains outside the published building price. |
| `all-in-one-cabins-garden-rooms.html` | What the single-room cabin starting prices cover, what to ask about assembly and VAT, and why the Corry's published size needs clarification. |

These are two maker comparisons, rather than five nearly identical product pages.
Each has original buying guidance, a comparison table, a clear price basis,
source links, unresolved questions and routes back to the parent Discovery.
The intended search role is maker/model research and related price/specification
questions. The existing Discovery remains the broad garden-rooms landing page;
the market pricing guide retains its separate comparison role. No search volume
or ranking opportunity is asserted for a maker without query evidence.

## Primary-source verification

Four primary pages were retrieved directly with HTTP 200 on 26 October 2026:

- https://www.conceptmodular.ie/showcase/standard-office
- https://www.conceptmodular.ie/showcase/signature-office
- https://www.conceptmodular.ie/solutions
- https://allinonecabins.ie/single-room-cabins/

The source register records their URLs, check date and hashes. Raw source copies
were retained only for internal QA; supplier HTML and photographs are not copied
into the release. Prices, material dimensions and fit-out details were compared
with those copies. Search snippets initially returned older Concept Modular
figures; the drafts use the directly retrieved pages. No catalogue price
correction is justified by those stale snippets.

The Corry area discrepancy remains unresolved and visible. No floor area is
calculated from dimensions, and no supplier marketing description is promoted
to a PlotNua finding about planning compliance, thermal performance or suitability
for sleeping. The two pages distinguish published information from PlotNua's
interpretation and from questions that still need a site-specific answer.

The new checks do not refresh the market pricing guide's older research snapshot
or extend its existing freshness deadline. A market-wide pricing refresh remains
a separate piece of work.

## Publication basis: decision required

This pilot proposes **factual, text-only editorial comparisons of public product
information**. It claims no supplier permission, partnership, endorsement,
commission, recommendation or photographic rights. No private correspondence,
contact history or internal record identifier appears in either page or its
public source register.

The existing text-only listing decision is explicitly scoped in
`atlas-tools/public-information-listings.json`:

> Wellness / Sauna only (DISC-001 Garden Retreat). Garden rooms and garden homes are untouched.

That decision is not silently extended here. Nor is the legacy publication
baseline treated as approval for new pages. Existing supplier permission,
objection, review and imagery gates remain in force and unchanged.

The founder's next publication decision should cover the two exact page drafts
and the proposed text-only garden-room editorial scope. Current authorised
organisation and outreach records were checked read-only on 26 October 2026;
their private contents are not reproduced here. Before switching to public/indexable
status, check for any intervening objection or review hold. Do not add a permission
record merely because a page has been approved by PlotNua.

The pages currently carry `noindex, nofollow` and a visible review label. Neither
is included in the sitemap, Search corpus or links on the public Discovery. The
builder refuses publication states and refuses exposure through those surfaces.
No production deployment is part of this PR.

## Exact proposed publication changes

Following approval and the current-hold check:

1. Record the narrow editorial publication decision separately from supplier
   permissions. Preserve all actual supplier holds and objections.
2. Remove the review labels and change the two pages to `index, follow`, through
   a reviewed release-mode change to their builder.
3. Add both canonical URLs to the sitemap with their actual modification dates.
4. Add a short **Maker guides** section on Living in the Garden, listing the two
   links alphabetically, with neutral descriptions and no change to Maker Explorer
   eligibility, order, imagery or recommendation logic.
5. Add the two pages to the site's approved informational Search corpus and update
   the sitemap page-count assertion in the Search rail builder. Re-run the existing
   corpus guards rather than changing their size limit speculatively.
6. Merge the approved release, verify exact live HTML and links, then inspect
   indexing through Search Console where available.

No country, town or model doorway pages, review scores, invented testimonials,
Offer/Product rich-result claims or availability guarantees are proposed.

## Validation completed

- Draft builder reproducibility and freshness checks pass.
- Identity, shared header and legacy Premium-builder locks pass.
- Existing garden authority checks pass (18/18).
- Existing pricing preservation proof and Search corpus checks pass.
- The image-rights HTML scan passes: no unpermitted supplier image introduced.
- Six deliberate faults are refused: publication state, invented permission,
  stale evidence, a substituted source domain, altered VAT and concealed size conflict.
- Chromium checks at 320, 390 and 1440 px pass: no page overflow, duplicate IDs or
  missing H1; JSON-LD parses, robots remain noindex, and all editorial internal
  links resolve. Comparison tables scroll within a labelled keyboard-focusable
  region on small screens.
- Desktop and mobile screenshots were inspected. The draft uses the existing
  Premium palette/components; its small stylesheet is scoped to these components.
- Browser checks block external requests, including analytics. These are local
  rendering checks, not a Core Web Vitals assessment.
- Editorial pass: plain homeowner language, short paragraphs, practical next
  questions, original comparison structure and qualifications beside the facts.
- `git diff --check` passes. Existing public page content, universes, rights records,
  sitemap and Search index remain byte-identical to the base.

Reproduce the principal checks:

```bash
python3 atlas-tools/build-garden-maker-pages.py --check
python3 atlas-tools/build-identity-stage1.py --check
python3 atlas-tools/prove-global-header.py
python3 atlas-tools/prove-premium-locks.py
python3 atlas-tools/prove-premium-garden-room-prices.py
node atlas-tools/prove-cluster1-garden-authority.mjs
python3 atlas-tools/build-search-index.py --check
node atlas-tools/validate-image-rights.js --scan-html . --permissions image-rights-manifest.json --max-age-days 30
git diff --check
```

## Local review

From the repository root:

```bash
python3 -m http.server 8000
```

- http://localhost:8000/concept-modular-garden-offices.html
- http://localhost:8000/all-in-one-cabins-garden-rooms.html

After publication, monitor each page's indexing and maker/model query impressions,
and its organic landings and engagement. Also track whether the linked Discovery
and market guide gain qualified visits. Two pages are a controlled pilot, not
evidence of a ranking improvement before Google has crawled and evaluated them.
