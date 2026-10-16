# Targeted publication — Elm Landscaping (Garden Rooms)

- Organisation: `recyCu5OjHlUObM8f` (Elm Landscaping (Garden Rooms))
- Scope: products `rec6AILkzDIDHZcO8`, `recN9555CIihkgea4`, `recQxXVefJDxeGWZz`, `recehpri9hsMl3Vyn`, `recsmHaT00C5d62O0`
- Atlas read: Atlas read 2026-10-16 via the Airtable MCP (base appoLZFWesvoPhZGR), REST shape built by mk_snap.py; read-only, sha256 `ee7b3ea6b992bbb4de0dca28934782aab8f5bc41e414690deee08bc7b2bc980c`
- Built on commit `bd043d651906`; tool atlas-tools/publish-targeted-update.py
- Mode: APPLY

## Where each product is published

- `rec6AILkzDIDHZcO8` — not published
- `recN9555CIihkgea4` — not published
- `recQxXVefJDxeGWZz` — not published
- `recehpri9hsMl3Vyn` — not published
- `recsmHaT00C5d62O0` — not published

## Living in the Garden (garden rooms)

- **NEW** `rec6AILkzDIDHZcO8` Elm Quin Contemporary Log Cabin
- **NEW** `recN9555CIihkgea4` Elm Tulla Contemporary Log Cabin
- **NEW** `recQxXVefJDxeGWZz` Elm Ruan Eco Garden Room
- **NEW** `recehpri9hsMl3Vyn` Elm Doughmore Studio Eco Garden Room
- **NEW** `recsmHaT00C5d62O0` Elm Doolin Contemporary Log Cabin

Header: sourceGardenRoomCount 575 → 580; eligibleCount 571 → 576; highConfidenceCount 146 → 151; confirmedIrishAvailabilityCount 264 → 269; priceEvidenceSummary {"verified": 275, "present-unverified":… → {"verified": 275, "present-unverified":…; organisationCount 62 → 63; governedDigest de6549b21f939eb85865a43388f31cb57b387e7… → d035cd4a77fbb62958eaa13ca60a1104e2e7f25…
Detail partitions updated: suppliers

## Supplier entry

- `.name`: <absent> → Elm Landscaping (Garden Rooms)
- `.locality`: <absent> → {"installationModel": "Nationwide by the supplier…
- `.organisationType`: <absent> → Supplier
- `.lastReviewed`: <absent> → 2026-08-28

## Imagery

- snapshot carries no Asset records; approved-image-assets-v1.json unchanged
- imagery pass:  13 product(s) now carry authorised imagery
- Every image is still decided by apply_authorised_imagery.py: live grant, scoped prefix, product link, required credit (+ photographer), link-back, medium.

## Maker Explorers, Search, homepage

- discovery-living-in-the-garden.html · gardenRooms figures {"products": 571, "makers": 62, "confirmed": 263, "noRoute": 43} → {"products": 576, "makers": 63, "confirmed": 268, "noRoute": 43}
- Search counts {"possibility": 13, "product": 698, "supplier": 62, "journey": 9} → {"possibility": 13, "product": 703, "supplier": 63, "journey": 9}
- Search universe pin re-frozen `19f846ef2522a3ad…` → `5d134a4e25f7946d…` (logged in governance/SEARCH-V1-CONTRACT.md)
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
- REVIEW prove-atlas-a —     PASS   the explanatory Phase 1 placements survive unchanged |     PASS   the AA-001 note names the lockup as the single brand exception |     PASS   the lockup carries no fill, border, radius or shadow |     PASS   no Atlas mark on any other page | ============================================================================ | FAILED — 2 check(s).

## Files that change

- atlas-tools/build-search-index.py
- discovery-living-in-the-garden.html
- garden-room-detail-index-v1.json
- garden-room-detail-suppliers-v1.json
- garden-room-recommendation-universe-v1.json
- governance/SEARCH-V1-CONTRACT.md
- search-index-v1.json
