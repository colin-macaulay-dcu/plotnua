# Garden maker guides: approved publication

Colin MacAulay approved both reviewed guides and their factual, text-only
publication scope on 26 October 2026. Deployment and live-verification evidence
are recorded in PR #3. This record supersedes the earlier draft review status.

## Released content

| Page | Homeowner purpose |
| --- | --- |
| `all-in-one-cabins-garden-rooms.html` | Compare three starting-price kits, identify what needs a written quotation, and retain the unresolved Corry size discrepancy. |
| `concept-modular-garden-offices.html` | Compare furnishing choices and distinguish building prices from VAT, site works and electrical connection. |

These are two original maker comparisons. Each includes a table, price basis,
primary-source links, practical questions and routes back to Living in the Garden.
The broad Discovery remains the garden-room landing page; the market pricing
comparison retains its separate role. No maker search volume or ranking gain
has been inferred without query evidence.

## Narrow editorial approval

`atlas-tools/maker-pages/publication.json` records approval for these two exact
pages only. It is a separate garden-room editorial decision; the existing
Wellness / Sauna register remains unchanged. No supplier permission, image
licence, partnership, endorsement or general catalogue expansion is asserted.

The builder imports the existing `derivePublicInformationListing` implementation.
Any applicable rights record is decided first: an objection, decline or review
hold cannot be overridden by the editorial register. Current authorised
organisation and outreach records were checked read-only on 26 October; private
contents and internal identifiers are not included in public artefacts.

No supplier photographs, product records, eligibility rules, recommendation
ordering or commercial relationships change. Existing analytics and consent
configuration are reused without settings changes.

## Discovery and indexing

- Both guides carry `index, follow`, self-canonicals, descriptive titles and
  descriptions, and WebPage/BreadcrumbList structured data. No Product, Offer,
  ratings or review claims are introduced.
- Both are listed once in the sitemap with 26 October modification dates.
- An early Maker Guides section links to them alphabetically from the Discovery,
  without altering the Maker Explorer.
- Two explicit informational Search records are added through `GUIDE_PAGES`.
  All previous records remain identical. Search runtime and topic expansion are
  unchanged; the 180 KiB size guard is unchanged.
- The Search rail scope assertion is deliberately updated from 22 to 24 public
  pages. Each new page carries the normal, hidden legacy mark anchor required
  by that builder, alongside the visible shared header.

## Evidence

Four maker-owned pages were retrieved directly with HTTP 200 on 26 October:

- https://www.conceptmodular.ie/showcase/standard-office
- https://www.conceptmodular.ie/showcase/signature-office
- https://www.conceptmodular.ie/solutions
- https://allinonecabins.ie/single-room-cabins/

The source register records URLs, dates and hashes. Material prices, dimensions
and fit-out details were checked against those retrieved pages. Stale search
snippets were rejected. Raw supplier HTML and photographs are not included.
The Corry discrepancy remains unresolved; no internal floor area or planning
compliance is calculated from marketing dimensions. Published information,
PlotNua's interpretation and questions for the maker remain distinct.

This check does not refresh the market pricing guide's older snapshot or extend
its existing freshness deadline. Its wider evidence refresh remains separate.

## Validation

The builder is reproducible and requires current evidence, the exact founder
approval, no supplier permission assertion, no imagery, and the canonical
rights-first gate. In check mode, each published guide must have exactly one
sitemap entry, parent link and informational Search record.

Passed: builder check; shared identity/header; all 12 Search rail guards; Premium
locks; pricing preservation; all 18 garden-authority checks; Search corpus guards;
image-rights scan; and whitespace validation. New guide queries return the intended
records, and every pre-existing Search record remains identical. The generated
index is 178,995 bytes, below its existing 180 KiB limit.

Chromium checks at 320, 390 and 1440 px verify indexable metadata, valid JSON-LD,
one H1, no duplicate IDs or page overflow, and labelled keyboard-focusable table
scrolling. Editorial links resolve. Desktop/mobile renders were inspected.
External requests, including analytics, were blocked during local browser QA.
These checks are not Core Web Vitals measurements.

Known pre-existing test issue: `prove-search-acceptance.mjs` expects a historical
artist product and crashes when reading the absent first result. It fails in the
same way with the untouched base index. This test and the underlying catalogue
are unchanged. Dedicated release checks verify existing record preservation and
the new maker/model search routes; the baseline failure is not presented as a pass.

## Verification after deployment

Check both live guides, the parent section, sitemap and Search index against the
approved repository bytes. Confirm HTTP 200, canonical URLs, index/follow metadata,
working links and absence of review labels. Retain the deployment result in PR #3.
Indexability is a technical state; Google indexing and ranking are not established
by a successful deployment. No Search Console indexing request is claimed here.

## Local preview

From the repository root:

```bash
python3 -m http.server 8000
```

- http://localhost:8000/all-in-one-cabins-garden-rooms.html
- http://localhost:8000/concept-modular-garden-offices.html

## Rollback

Revert the merged release as a unit: guides, source/approval configuration,
parent links, sitemap, Search allowlist/index and header/identity registrations.
No database migration or analytics-settings rollback is required.
