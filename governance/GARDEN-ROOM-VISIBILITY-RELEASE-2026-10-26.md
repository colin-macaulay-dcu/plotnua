# Garden room visibility: first implementation

Status: draft for review; no production deployment authorised by this record.
Base: `0422dd147e039d66683d4ec5dad01bc1c53e4a66`.

## What changes for a visitor

The Living in the Garden page gains an early section, **Comparing garden rooms
in Ireland?**, with direct routes to makers, the published-price guide and the
existing planning conditions. It also gives practical questions for somebody
choosing an office for daily use: insulation, glazing, ventilation, heating,
power, internet, access and what the site-specific quote includes.

A normal HTML link makes the existing public TRIQ QUBE product page discoverable
from the garden-room hub. The surrounding text preserves the important limits:
the price is German-market, delivery to an Irish address needs confirmation,
and Irish installation has not been established. This is an example of a
construction system, not a recommendation or a change to Maker Explorer eligibility.

The pricing guide states that it covers detached garden rooms and offices,
rather than extensions or attached sunrooms. The existing published price answer
still comes first. This clarifies scope; whether it changes query relevance is
an inference to test after release, not an established diagnosis.

## Evidence and implementation boundaries

- All original pricing ranges, counts, VAT cautions and research dates remain.
- Page modification dates and the two sitemap entries move to 26 October;
  the underlying research snapshot remains 7 October, corrected on 20 October.
- The price builder owns the generated date and structured-data changes.
- The Premium preservation proof declares exactly two new scope sentences and
  exactly one structured-data date change. Its frozen baseline is unchanged.
- The planning mutation test's sitemap anchor follows the new page date.
- Existing assessment journeys, analytics, consent, imagery, product records,
  publication eligibility and preview pages are unchanged.
- No new legal or statutory interpretation is introduced.

The added editorial section is authored HTML outside the existing builder-owned
regions. Legacy layout builders remain locked; bounded maker and price builders
continue to pass their checks.

## Validation

Passed locally:

```text
python3 atlas-tools/prove-premium-garden-room-prices.py
python3 atlas-tools/prove-premium-garden-room-prices-capability.py
node atlas-tools/prove-cluster1-garden-authority.mjs
node atlas-tools/prove-cluster1-capability.mjs
python3 atlas-tools/build-maker-explorer.py --check
python3 atlas-tools/prove-premium-locks.py
git diff --check
```

The price capability proof catches all 33 planted faults. The garden authority
proof passes all 18 checks; its capability proof catches all 19 planted faults.

Chromium checks at 320, 390 and 1440 pixels pass on both changed pages: no horizontal
overflow, no duplicate IDs, one H1 and valid JSON-LD. The new planning anchor and
TRIQ navigation both work. Desktop and mobile screenshots were visually reviewed.
External requests were blocked during local browser checks, so those visits did
not send analytics events. These are layout/navigation checks, not Core Web Vitals.

Editorial review: the new copy gives a useful next step on first reading, uses
short paragraphs and ordinary homeowner language, frames specifications as
questions, and keeps the product's Irish-market limitations beside its link.

Known pre-existing check limitation: `build-seo-phase1.py --check` requests sitemap
changes even on the untouched base in this shallow checkout. Its historical
site-wide date calculation is not a release gate for this patch; running it in
write mode would change unrelated dates. The dedicated page/sitemap date proof
passes. No site-wide builder rewrite is included here.

## Release and measurement

Review the diff and approve this batch before merging into the production branch.
After publication, verify the live HTML and request inspection of the hub and
pricing page in Search Console. No indexing request has been submitted here.

Use the audit's existing account baseline privately. Measure Ireland/Web results
for the hub and pricing page, including exact queries and related variants;
compare clicks, impressions, CTR and position over equal complete periods.
Review weekly and use a complete 28-day window for the first substantive
comparison, accounting for Google's reporting delay and small samples. Also
compare production-hostname organic landing sessions and engagement in GA4.

The next workstream is a small, evidence-complete set of indexable product or
maker pages, with clear specifications, price basis, Irish availability and
ordinary internal links. Refresh the pricing evidence before its current
freshness deadline of 7 November; this release does not extend that deadline.
Conversion definitions and development-traffic exclusion require their own
reviewable analytics proposal before settings change.

First-page visibility and qualified organic visits are progress measures.
First place is an ambition; neither this patch nor a publication date guarantees it.

## Search guidance used

Google recommends descriptive crawlable internal links and useful content written
for people. This release implements those practices without treating either as
a guaranteed ranking outcome:

- https://developers.google.com/search/docs/crawling-indexing/links-crawlable
- https://developers.google.com/search/docs/fundamentals/creating-helpful-content

## Rollback

Revert this release commit as a unit, restoring the two page dates, sitemap entries,
builder dates and preservation declarations together. No data migration or
analytics rollback is needed.
