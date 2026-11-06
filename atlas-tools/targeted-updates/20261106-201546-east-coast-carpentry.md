# Targeted publication — East Coast Carpentry

- Organisation: `reczQAlAQhP3hs9qN` (East Coast Carpentry)
- Scope: products `rec45XRwQ4qqGCQbv`, `rec7SV0aGZjcDYmF7`, `rec8hgSQtX38xqHdZ`, `recCF6Fdi2i1Qo04Z`, `recMklMPlZN6DAmwc`, `recN0bJ1hnq0gaZ2R`, `recXNnHMEexJKnLGA`, `reccTIKHePHQoK7XX`, `rechrLK9CR0ukDXrY`, `reclM4VYSSq9lsMtp`
- Atlas read: Read-only scoped Atlas read via the Airtable connector, 6 November 2026, after the founder-approved Stage 3B East Coast Carpentry Atlas additions (6 Nov 2026 19:10 approval). Converted to the REST shape by conn2rest.py; values copied unaltered., sha256 `528d531b539fdeadee96f960c856bcbc1be11c029b1521eab6839aa2daa9a31b`
- Built on commit `f788526142e6`; tool atlas-tools/publish-targeted-update.py
- Provenance note (6 Nov 2026): `f788526142e6` is a local scratch commit in a remote-less clone, never pushed: production `34085fa` plus this candidate's Stage 3B source changes (the hold register with the ECC holds and the D1(b) `region` field, the generator, your-plot.html, build-maker-explorer.py, maker-explorer.js, the publisher's A-Z regional-line allowance, living-garden-added.json and the proofs). The tool refuses an uncommitted tree. The supplier-gallery header was then rebuilt with atlas-tools/build-supplier-gallery.py. Snapshot: connector reads converted in arrival order.
- Mode: APPLY

## Where each product is published

- `rec45XRwQ4qqGCQbv` — not published
- `rec7SV0aGZjcDYmF7` — not published
- `rec8hgSQtX38xqHdZ` — not published
- `recCF6Fdi2i1Qo04Z` — not published
- `recMklMPlZN6DAmwc` — not published
- `recN0bJ1hnq0gaZ2R` — not published
- `recXNnHMEexJKnLGA` — not published
- `reccTIKHePHQoK7XX` — not published
- `rechrLK9CR0ukDXrY` — not published
- `reclM4VYSSq9lsMtp` — not published

## Living in the Garden (garden rooms)

- **NEW** `rec45XRwQ4qqGCQbv` Premium Composite Garden Room 3m × 3m
- **NEW** `rec7SV0aGZjcDYmF7` Value Timber Garden Room 5m × 5m
- **NEW** `rec8hgSQtX38xqHdZ` Premium Composite Garden Room 5m × 4m
- **NEW** `recCF6Fdi2i1Qo04Z` Value Timber Garden Room 3m × 3m
- **NEW** `recMklMPlZN6DAmwc` Premium Composite Garden Room 4m × 3m
- **NEW** `recN0bJ1hnq0gaZ2R` Premium Composite Garden Room 5m × 3m
- **NEW** `recXNnHMEexJKnLGA` Value Timber Garden Room 4m × 3m
- **NEW** `reccTIKHePHQoK7XX` Value Timber Garden Room 5m × 3m
- **NEW** `rechrLK9CR0ukDXrY` Premium Composite Garden Room 5m × 5m
- **NEW** `reclM4VYSSq9lsMtp` Value Timber Garden Room 5m × 4m

Header: sourceGardenRoomCount 582 → 592; eligibleCount 570 → 580; highConfidenceCount 154 → 164; confirmedIrishAvailabilityCount 274 → 284; priceEvidenceSummary {"verified": 270, "present-unverified":… → {"verified": 280, "present-unverified":…; organisationCount 64 → 65; governedDigest 2231b53a7ff2466b20b70013e6975690427ae0a… → 5ba762706598d6a4bb18f12cc145838a0becd0d…
Detail partitions updated: considerations

## Imagery

- snapshot carries no Asset records; approved-image-assets-v1.json unchanged
- imagery pass:  15 product(s) now carry authorised imagery
- Every image is still decided by apply_authorised_imagery.py: live grant, scoped prefix, product link, required credit (+ photographer), link-back, medium.

## Maker Explorers, Search, homepage

- discovery-living-in-the-garden.html · gardenRooms figures {"products": 570, "makers": 64, "confirmed": 270, "noRoute": 43} → {"products": 580, "makers": 65, "confirmed": 280, "noRoute": 43}
- Search counts {"possibility": 25, "product": 705, "supplier": 64, "journey": 9} → {"possibility": 25, "product": 715, "supplier": 65, "journey": 9}
- Search universe pin re-frozen `52a51130414f05db…` → `1be874ad227c76a2…` (logged in governance/SEARCH-V1-CONTRACT.md)
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
- OK prove-atlas-a

## Files that change

- atlas-tools/build-search-index.py
- discovery-living-in-the-garden.html
- garden-room-detail-considerations-v1.json
- garden-room-detail-evidence-v1.json
- garden-room-detail-index-v1.json
- garden-room-recommendation-universe-v1.json
- governance/SEARCH-V1-CONTRACT.md
- search-index-v1.json
