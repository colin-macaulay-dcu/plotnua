# Garden Rooms Ireland: search-focus revision

Status: prepared for founder review; not approved for production deployment.

Request: 26 October 2026, prioritise “garden rooms Ireland” and “garden rooms in Ireland”; continue preparing the proposed landing-page improvements.

## Problem and resulting behaviour

The existing page already mentioned Ireland in its title, but its hero led with the broad Discovery question and its article began with the statutory summary. This revision makes “Garden Rooms in Ireland” the main heading and brings buying guidance and the two existing maker guides before the intact planning summary. It keeps the established URL and canonical.

The title becomes “Garden Rooms in Ireland: Compare Makers & Prices | PlotNua”. The description and WebPage name follow that scope. The Discovery question remains in the hero as its secondary line. Social-sharing editorial copy is preserved.

The two maker links become a factual comparison of published format, price basis and installation questions. This is explicitly two examples, not a best-supplier ranking or a complete market comparison. Facts trace to the already published maker guides and atlas-tools/maker-pages/source-evidence.json, checked 26 October 2026. No new numerical price, supplier image, supplier permission, partnership, availability confirmation or planning finding is introduced.

The homepage’s existing garden-room card gains descriptive link text. Both maker guides gain descriptive return links through their shared generator. The Search index is rebuilt; only poss-living-in-the-garden changes among its records. Counts and product data stay the same.

## Scope and preservation

This branch is based on production commit 1062e523412a1be34b88a804e522c1c4f1c63ef7. The separate, approved 59-record Airtable correction has already been executed, but its local catalogue candidate is not part of this branch. Neither that candidate nor the anonymous pricing-guide correction is deployed by this revision.

All page bytes from the Opportunity section onwards are identical to the base page. The planning summary text is identical and moved as a block. Every image, non-JSON-LD script, existing ID and link destination on the main page is preserved. Global header, Premium assets, hero interaction, assessments, analytics settings, supplier eligibility and evidence universes are unchanged. The page and sitemap already carry the actual revision date, 26 October 2026, so no unrelated timestamps are advanced.

The J1 claim guard changes only its exact H1/title declarations to the new expected values. No planning or price guard is relaxed. The legacy SEO builder’s metadata declarations follow the new values; its writing mode is not used.

## Validation

- Cluster 1 claim guards: 18/18 pass; capability proof: 19/19 planted faults caught.
- Maker guide generator: --check passes, retaining the rights-first publication gate.
- Identity layer and global header: pass.
- Premium locks and Premium pricing-page preservation: pass.
- Search builder: --check passes; index 179,015 bytes, below the 180 KiB limit. All unrelated Search records remain identical.
- Search rail: all 12 guards pass.
- Image rights: 128 publishable references, zero refused.
- Browser checks at widths 320, 390 and 1440: one visible H1; no horizontal document overflow or duplicate IDs; structured data parses; comparison overflow contained; maker-guide links, return links, planning jump and homepage link work.
- Visual inspection: mobile hero and comparison retain the established Premium presentation. The comparison is horizontally scrollable on narrow screens, with a focusable, labelled region.
- git diff --check passes.

Known pre-existing limitation: build-seo-phase1.py --check refuses on the retired “If you want the conditions in full.” anchor. The same refusal is reproduced on the production-based original checkout. This historical builder is not the release gate; its writing mode was not run. Current claim, identity, search and maker gates pass.

## Measurement and release

The Google ranking baseline was recorded on 26 October 2026, with latest returned Search Console data through 24 October. Neither exact head query has a confirmed named-query position in that extract. This revision makes no ranking claim. Retain the baseline and compare consistent Ireland/Web periods, exact queries, devices, landing pages, impressions and clicks after deployment. Qualified enquiries remain the business outcome.

Founder approval is still required before merging this draft and deploying it. No GSC indexing request or production change has been made by this branch.
