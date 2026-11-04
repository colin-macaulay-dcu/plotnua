# Targeted publication — Gardenhouse24 Ireland

- Organisation: `reclA5R4kPCCwc8Pc` (Gardenhouse24 Ireland)
- Scope: products `rec0aKJXY0kwObDF4`, `rec3TWaGevhGnoTxq`, `recEDHcHJ5dWaWklV`, `recdDCBpXBKOa7leI`, `reckCDHkLz2m4pIln`, `recry2T2pKMwGZkIU`
- Atlas read: Atlas read 2026-11-04T11:40Z via the Airtable connector (read-back of the six records created under founder authorisation 4 Nov 2026, 'Supplier integration Phase 2'); REST shape, sha256 `9199a3bbc373333effdd4afe31a1e1d672b6bd9cd6bac0ce754d2a97ed07e62f`
- Built on commit `f77883e1d455`; tool atlas-tools/publish-targeted-update.py
- Mode: APPLY

## Where each product is published

- `rec0aKJXY0kwObDF4` — not published
- `rec3TWaGevhGnoTxq` — not published
- `recEDHcHJ5dWaWklV` — not published
- `recdDCBpXBKOa7leI` — not published
- `reckCDHkLz2m4pIln` — not published
- `recry2T2pKMwGZkIU` — not published

## Garden Retreat (wellness)

- **NEW** `rec0aKJXY0kwObDF4` Hot Tub DeLux 220
- **NEW** `rec3TWaGevhGnoTxq` TALLEBORG 70 sauna cabin with large windows
- **NEW** `recEDHcHJ5dWaWklV` Hot Tub DeLux 200
- **NEW** `recdDCBpXBKOa7leI` BENE 70 garden sauna room with a lounge room
- **NEW** `reckCDHkLz2m4pIln` MOSSO 70 outdoor sauna cabin with terrace
- **NEW** `recry2T2pKMwGZkIU` LEO barrel sauna, front full glass

Header: snapshotScope Atlas Core appoLZFWesvoPhZGR via the Ai… → Atlas Core appoLZFWesvoPhZGR via the Ai…; sourceCategoryCount 158 → 164; eligibleCount 122 → 128; organisationCount 7 → 8; kindCounts {"sauna": 93, "hot-tub": 22, "cold-plun… → {"sauna": 97, "hot-tub": 24, "cold-plun…; kindOrganisationCounts {"sauna": 6, "hot-tub": 4, "cold-plunge… → {"sauna": 7, "hot-tub": 5, "cold-plunge…; listingBasisCounts {"SUPPLIER_PERMISSION": 37, "PUBLIC_INF… → {"SUPPLIER_PERMISSION": 43, "PUBLIC_INF…

## Imagery

- snapshot carries no Asset records; approved-image-assets-v1.json unchanged
- imagery pass:  15 product(s) now carry authorised imagery
- Every image is still decided by apply_authorised_imagery.py: live grant, scoped prefix, product link, required credit (+ photographer), link-back, medium.

## Maker Explorers, Search, homepage

- discovery-garden-retreat.html · saunas figures {"products": 93, "makers": 6, "confirmed": 0, "noRoute": 0} → {"products": 97, "makers": 7, "confirmed": 0, "noRoute": 0}
- discovery-garden-retreat.html · hotTubs figures {"products": 22, "makers": 4, "confirmed": 0, "noRoute": 0} → {"products": 24, "makers": 5, "confirmed": 0, "noRoute": 0}
- Search counts {"possibility": 21, "product": 699, "supplier": 64, "journey": 9} → {"possibility": 21, "product": 705, "supplier": 64, "journey": 9}
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
- OK prove-atlas-a

## Files that change

- discovery-garden-retreat.html
- search-index-v1.json
- wellness-universe-v1.json
