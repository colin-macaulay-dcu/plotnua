# Shomera maker guide: release review

Status: draft PR; production publication pending founder approval.

## Result and purpose

The prepared Shomera editorial draft is integrated with the existing maker-guide renderer. It compares six Classic and Contemporary examples, their advertised starting prices, published dimensions and the scope of building/installation. It links back to Garden Rooms in Ireland and the quotation checklist. The proposed third comparison row is atlas-tools/maker-pages/shomera-parent-entry.html.

The page is noindex/nofollow, carries a visible review label, and is absent from the parent page, sitemap and Search index. Do not merge this draft as a publication release. The proposed row is a source fragment, not an active navigation link. The original two-guide publication approval is preserved exactly; the separate Shomera decision is PENDING with no named approval or decision date.

This work supports the main garden-room comparison. It does not claim an improvement for “garden rooms Ireland” or a supplier endorsement. No supplier imagery is used.

## Evidence and limitations

Nine public Shomera pages were directly checked on 26 October 2026, including each of the six model pages. Their factual evidence and hashes are in shomera-evidence.json. Tables derive from that evidence, not hardcoded HTML prices. Each product page explicitly includes building and installation in its starting price. VAT remains unconfirmed; starting prices are not site quotations. The copy distinguishes model names from usable area and explains that decoration and external landscaping need separate attention.

The shared wrapper still uses the two-guide pilot’s default substitutions for its unchanged templates. Shomera supplies its own table substitutions; none of the pilot price facts appears in Shomera’s template. Existing two-guide output remains byte-identical. The new builder checks its own sources, models, scope limitations, evidence age, pending approval state and absence from public discovery surfaces. Once a real approval is recorded, its publication branch uses the existing canonical rights-first derivation; it does not override an objection, decline or review hold.

No Airtable, analytics or supplier-contact writes are part of this branch. The separate 59-record Airtable correction and its unpublished catalogue candidate are outside it.

## Validation

- Both existing maker pages reproduce exactly; their original approval file is unchanged.
- New Shomera builder --check passes.
- Identity and global header checks pass for 26 identity pages / 28 header pages.
- Main-page claim guards: 18/18 pass.
- Search index and Search rail checks pass. Public sitemap remains 24 URLs; Search bytes are unchanged.
- Premium builder locks and Premium pricing preservation pass.
- Negative checks refuse invented draft approval, VAT relabelling and exposure of the draft through the main page.
- Browser checks at widths 320, 390 and 1440: one H1, labelled scrollable table, no horizontal document overflow, no duplicate IDs, valid JSON-LD and noindex/nofollow. Source and navigation links have visible text.
- Main garden-room page, the two published maker pages, sitemap, Search index and recommendation universe are byte-identical to production base 7e37ca697d1d0a3c6a5265482a31f4e8fcbef23d.

## Exact publication steps after approval

1. Record the founder’s actual approval of this guide and third comparison entry in shomera-publication.json; set its source publication status to PUBLISHED. Recheck current supplier objection/review state before deriving publication visibility. Do not infer image permission.
2. Add the reviewed row to the main comparison table; change “These two researched examples” to “These three researched examples” and “For either route” to “For each route”. Preserve all planning content and existing maker entries.
3. Add the one canonical sitemap URL and one informational GUIDE_PAGES Search entry (existing possibility shape), then rebuild Search. Deliberately update the Search rail’s expected public-page count from 24 to 25 and the Search contract. Do not change recommendation records or ranking logic.
4. Rebuild the Shomera page and rerun the relevant page, publication, identity/header, Search, rights and responsive checks. Confirm the only new Search record is the Shomera guide and all existing records remain identical.
5. Present the resulting reviewed head and successful checks; merge only within the founder’s approval scope. Verify production bytes after deployment.

## Main-page indexing checkpoint

The founder’s Search Console screenshot on 26 October confirms the main garden-room URL is indexed, crawl/indexing allowed, successful fetch and the inspected URL selected as canonical. The last recorded crawl is 20 October 2026 at 16:56:49, before the 26 October changes. The founder reports requesting indexing for the updated page. A later crawl and processing of the revised content have not yet been confirmed. The live sitemap returns HTTP 200, parses, and lists the main page with lastmod 2026-10-26. The screenshot’s sitemap processing warning is not treated as proof of a malformed live sitemap.

Next research task after the Shomera release: resolve the differing Garden Office Solutions guide and shop prices before using them in another comparison. Outreach candidates remain research only; no messages are authorised or sent.
