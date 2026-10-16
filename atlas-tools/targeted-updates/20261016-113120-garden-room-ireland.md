# Targeted publication — Garden Room Ireland

- Organisation: `recUrpkOqKbynjQP0` (Garden Room Ireland)
- Scope: products `recs7YJnVX29hkueM`
- Atlas read: Atlas read 2026-10-16 via the Airtable MCP (base appoLZFWesvoPhZGR), REST shape built by mk_snap.py; read-only, sha256 `a40f310291c567866125ca61cf8cd0e455618c44143d0d15bb32c87bebd89a4d`
- Built on commit `dcc752e70ae9`; tool atlas-tools/publish-targeted-update.py
- Mode: APPLY

## Where each product is published

- `recs7YJnVX29hkueM` — not published

## Living in the Garden (garden rooms)

- **NEW** `recs7YJnVX29hkueM` Garden Room Ireland QC6

Header: sourceGardenRoomCount 581 → 582; eligibleCount 577 → 578; highConfidenceCount 152 → 153; confirmedIrishAvailabilityCount 270 → 271; priceEvidenceSummary {"verified": 275, "present-unverified":… → {"verified": 275, "present-unverified":…; organisationCount 64 → 65; governedDigest f84965dac3727397fc56dcaaeabdda72433daab… → 22708a8281fa8d7dfead0d6f0246a43d86f5b65…
Detail partitions updated: suppliers

## Supplier entry

- `.name`: <absent> → Garden Room Ireland
- `.locality`: <absent> → {"installationModel": "The supplier states its st…
- `.organisationType`: <absent> → Supplier
- `.lastReviewed`: <absent> → 2026-08-28

## Imagery

- snapshot carries no Asset records; approved-image-assets-v1.json unchanged
- imagery pass:  13 product(s) now carry authorised imagery
- Every image is still decided by apply_authorised_imagery.py: live grant, scoped prefix, product link, required credit (+ photographer), link-back, medium.

## Maker Explorers, Search, homepage

- discovery-living-in-the-garden.html · gardenRooms figures {"products": 577, "makers": 64, "confirmed": 269, "noRoute": 43} → {"products": 578, "makers": 65, "confirmed": 270, "noRoute": 43}
- Search counts {"possibility": 13, "product": 704, "supplier": 64, "journey": 9} → {"possibility": 13, "product": 705, "supplier": 65, "journey": 9}
- Search universe pin re-frozen `b7b864535d43c475…` → `3821b6487d670f08…` (logged in governance/SEARCH-V1-CONTRACT.md)
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
- PRE-EXISTING prove-atlas-a — e unchanged |     PASS   the AA-001 note names the lockup as the single brand exception |     PASS   the lockup carries no fill, border, radius or shadow |     PASS   no Atlas mark on any other page | ============================================================================ | FAILED — 2 check(s).

## Files that change

- atlas-tools/build-search-index.py
- discovery-living-in-the-garden.html
- garden-room-detail-index-v1.json
- garden-room-detail-suppliers-v1.json
- garden-room-recommendation-universe-v1.json
- governance/SEARCH-V1-CONTRACT.md
- search-index-v1.json
