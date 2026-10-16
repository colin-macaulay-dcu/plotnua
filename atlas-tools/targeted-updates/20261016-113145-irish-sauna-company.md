# Targeted publication — Irish Sauna Company

- Organisation: `recLW0vZbkBGPRkZ9` (Irish Sauna Company)
- Scope: products `recJlhoNav6YNU1zj`
- Atlas read: Atlas read 2026-10-16 via the Airtable MCP (base appoLZFWesvoPhZGR), REST shape built by mk_snap.py; read-only, sha256 `35695f8a4916c3fcdc2a18259e38017b47f46b919a30b60ba1f781e30d946b71`
- Built on commit `72e65a649901`; tool atlas-tools/publish-targeted-update.py
- Mode: APPLY

## Where each product is published

- `recJlhoNav6YNU1zj` — not published

## Garden Retreat (wellness)

- **NEW** `recJlhoNav6YNU1zj` Harvia Legend Wood-Burning Outdoor Sauna (supplied by Irish Sauna Company)

Header: snapshotScope Atlas Core appoLZFWesvoPhZGR via the Ai… → Atlas Core appoLZFWesvoPhZGR via the Ai…; sourceCategoryCount 153 → 154; heldCount 21 → 22

## Imagery

- snapshot carries no Asset records; approved-image-assets-v1.json unchanged
- imagery pass:  13 product(s) now carry authorised imagery
- Every image is still decided by apply_authorised_imagery.py: live grant, scoped prefix, product link, required credit (+ photographer), link-back, medium.

## Maker Explorers, Search, homepage

- Search counts {"possibility": 13, "product": 705, "supplier": 65, "journey": 9} → {"possibility": 13, "product": 705, "supplier": 65, "journey": 9}
- Homepage figures (index.html, atlas-stats.json) are the whole-Atlas census written by atlas-stats.yml, not publication counts: untouched by design.

## Validation

- OK validate_garden_room_universe
- OK validate_garden_room_detail_evidence
- OK detail partitions + index
- OK imagery guards (--prove)
- OK image-rights manifest matches records
- OK image-rights gate (scan-html)
- OK image provenance
- OK maker explorer --check
- OK search index --check
- OK maker product links --check
- OK preview-request hold --check
- OK test_wellness_universe
- PRE-EXISTING prove-atlas-a — e unchanged |     PASS   the AA-001 note names the lockup as the single brand exception |     PASS   the lockup carries no fill, border, radius or shadow |     PASS   no Atlas mark on any other page | ============================================================================ | FAILED — 2 check(s).

## Files that change

- search-index-v1.json
- wellness-universe-v1.json
