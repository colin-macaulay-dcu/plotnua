# Targeted publication — NOOK Prefab (espacio NOOK)

- Organisation: `recmBdXALBPGk5wSI` (NOOK Prefab (espacio NOOK))
- Scope: products `recDa5vihxcYG9xoH`, `rectQX4XpBbD6H3LU`
- Atlas read: Read-only scoped Atlas read via the Airtable connector, 6 November 2026, after founder-approved NOOK Stage 3A Atlas corrections (6 Nov 2026 14:26 approval). Converted to the REST shape by conn2rest.py; values copied unaltered., sha256 `179f544af1f1e80bdb291ceeb3160a2eef08cb77d23c77c22422de188f28c7c8`
- Built on commit `0ada01349d8d`; tool atlas-tools/publish-targeted-update.py
- Provenance note (6 Nov 2026): `0ada01349d8d` is a local scratch commit in a remote-less clone, never pushed: production `d02ee8a5c629` plus this candidate's price-presentation hold code (generator, your-plot.html, build-maker-explorer.py, the parity proof and atlas-tools/price-presentation-holds.json). The tool refuses an uncommitted tree, and the founder's instruction was to stop before committing. Snapshot: connector reads converted in arrival order (see the Stage 3A candidate report).
- Mode: APPLY

## Where each product is published

- `recDa5vihxcYG9xoH` — atlas-match-pool.json, atlas-recognition-pool.json, discovery-living-in-the-garden.html, garden-room-detail-alternatives-v1.json, garden-room-detail-bestfor-v1.json, garden-room-detail-considerations-v1.json, garden-room-detail-evidence-v1.json, garden-room-detail-planningconsiderations-v1.json, garden-room-detail-sources-v1.json, garden-room-detail-strengths-v1.json, garden-room-detail-typicalhomeowner-v1.json, garden-room-recommendation-universe-v1.json, search-index-v1.json
- `rectQX4XpBbD6H3LU` — atlas-recognition-pool.json, discovery-living-in-the-garden.html, garden-room-detail-alternatives-v1.json, garden-room-detail-bestfor-v1.json, garden-room-detail-considerations-v1.json, garden-room-detail-evidence-v1.json, garden-room-detail-planningconsiderations-v1.json, garden-room-detail-sources-v1.json, garden-room-detail-strengths-v1.json, garden-room-detail-typicalhomeowner-v1.json, garden-room-recommendation-universe-v1.json, search-index-v1.json

## Living in the Garden (garden rooms)

- changed `recDa5vihxcYG9xoH` NOOK 10
    - `.name`: NOOK Base 9.75m² (Open Plan) → NOOK 10
    - `.productName`: NOOK Base 9.75m² (Open Plan) → NOOK 10
    - `.productUrl`: null → https://nookprefab.com/pages/nook-base-garden-room
    - `.qualification.priceEvidence`: present-unverified → verified
    - `.qualification.reasons`: ["Supplier attribution is confirmed: NOOK Prefab (espacio N… → ["A verified price is recorded.", "A product-level source i…
    - `.qualification.caveats`: ["Irish availability is not yet confirmed. Nothing establis… → ["Irish availability is not yet confirmed. Nothing establis…
    - `.qualification.evidenceSignals.price`: present-unverified → verified
    - `.qualification.evidenceSignals.source`: supplier-level → product-level
    - `.qualification.evidenceSignals.productUrl`: missing → present
    - `.qualification.evidenceSignals.productEvidenceCompleteness`: Blocked — Core Attribution or Evidence Missing → Product Evidence Complete — Organisation Gate Required
    - `.priceEvidence.priceType`: Custom Quote → Starting From
    - `.priceEvidence.status`: Researching → Verified
    - `.priceEvidence.includesVat`: null → No
    - `.priceEvidence.evidenceScope`: null → Product-Specific
    - … 18 more field(s)
- changed `rectQX4XpBbD6H3LU` NOOK 20
    - `.name`: NOOK Double 19.5m² (Open Plan) → NOOK 20
    - `.productName`: NOOK Double 19.5m² (Open Plan) → NOOK 20
    - `.productUrl`: null → https://nookprefab.com/pages/nook-double-garden-room/
    - `.qualification.priceEvidence`: quote-only → verified
    - `.qualification.reasons`: ["This product is priced by quotation, as the supplier publ… → ["A verified price is recorded.", "A product-level source i…
    - `.qualification.caveats`: ["Irish availability is not yet confirmed. Nothing establis… → ["Irish availability is not yet confirmed. Nothing establis…
    - `.qualification.evidenceSignals.price`: quote-only → verified
    - `.qualification.evidenceSignals.source`: supplier-level → product-level
    - `.qualification.evidenceSignals.productUrl`: missing → present
    - `.qualification.evidenceSignals.productEvidenceCompleteness`: Blocked — Core Attribution or Evidence Missing → Product Evidence Complete — Organisation Gate Required
    - `.priceEvidence.base`: null → 59000
    - `.priceEvidence.priceType`: Custom Quote → Starting From
    - `.priceEvidence.status`: Researching → Verified
    - `.priceEvidence.includesVat`: null → No
    - … 25 more field(s)

Header: priceEvidenceSummary {"verified": 268, "present-unverified":… → {"verified": 270, "present-unverified":…; quoteOnlyPriceCount 20 → 19; governedDigest 1b5ef07c7fea82981de7e36a2865cb224042467… → 2231b53a7ff2466b20b70013e6975690427ae0a…; missingProductUrlCount 170 → 168
Detail partitions updated: considerations, strengths

## Imagery

- snapshot carries no Asset records; approved-image-assets-v1.json unchanged
- imagery pass:  15 product(s) now carry authorised imagery
- Every image is still decided by apply_authorised_imagery.py: live grant, scoped prefix, product link, required credit (+ photographer), link-back, medium.

## Maker Explorers, Search, homepage

- Search counts {"possibility": 25, "product": 705, "supplier": 64, "journey": 9} → {"possibility": 25, "product": 705, "supplier": 64, "journey": 9}
- Search universe pin re-frozen `51394c35c3daec51…` → `52a51130414f05db…` (logged in governance/SEARCH-V1-CONTRACT.md)
- Homepage figures (index.html, atlas-stats.json) are the whole-Atlas census written by atlas-stats.yml, not publication counts: untouched by design.
- Also referenced in atlas-match-pool.json (legacy match pool): not a Discovery surface, not changed.
- Also referenced in atlas-recognition-pool.json (identity catalogue (generate_recognition_pool.py)): not a Discovery surface, not changed.

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
- garden-room-detail-strengths-v1.json
- garden-room-recommendation-universe-v1.json
- governance/SEARCH-V1-CONTRACT.md
- search-index-v1.json
