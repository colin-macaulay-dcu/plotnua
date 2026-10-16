# Targeted publication — Don Modular Homes

- Organisation: `recOLYgRSUdzU8zwI` (Don Modular Homes)
- Scope: products `recjMsY7TFKaadyQV`
- Atlas read: Atlas read 2026-10-16 via the Airtable MCP (base appoLZFWesvoPhZGR), REST shape built by mk_snap.py; read-only, sha256 `1680e6bcd5dad6d4a9a8b670b510d56a9339ab8771d8a975be4901df60c539ac`
- Built on commit `7662e5a8bb4e`; tool atlas-tools/publish-targeted-update.py
- Mode: APPLY

## Where each product is published

- `recjMsY7TFKaadyQV` — not published

## Living in the Garden (garden rooms)

- **NEW** `recjMsY7TFKaadyQV` Don Modular Garden Room

Header: sourceGardenRoomCount 580 → 581; eligibleCount 576 → 577; highConfidenceCount 151 → 152; confirmedIrishAvailabilityCount 269 → 270; priceEvidenceSummary {"verified": 275, "present-unverified":… → {"verified": 275, "present-unverified":…; organisationCount 63 → 64; governedDigest d035cd4a77fbb62958eaa13ca60a1104e2e7f25… → f84965dac3727397fc56dcaaeabdda72433daab…
Detail partitions updated: none

## Imagery

- snapshot carries no Asset records; approved-image-assets-v1.json unchanged
- imagery pass:  13 product(s) now carry authorised imagery
- Every image is still decided by apply_authorised_imagery.py: live grant, scoped prefix, product link, required credit (+ photographer), link-back, medium.

## Maker Explorers, Search, homepage

- discovery-living-in-the-garden.html · gardenRooms figures {"products": 576, "makers": 63, "confirmed": 268, "noRoute": 43} → {"products": 577, "makers": 64, "confirmed": 269, "noRoute": 43}
- Search counts {"possibility": 13, "product": 703, "supplier": 63, "journey": 9} → {"possibility": 13, "product": 704, "supplier": 64, "journey": 9}
- Search universe pin re-frozen `5d134a4e25f7946d…` → `b7b864535d43c475…` (logged in governance/SEARCH-V1-CONTRACT.md)
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
- garden-room-recommendation-universe-v1.json
- governance/SEARCH-V1-CONTRACT.md
- search-index-v1.json
