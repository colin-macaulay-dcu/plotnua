# Targeted publication — Outdoor Living (ModPod)

- Organisation: `recn9B3Qn43VUXxAg` (Outdoor Living (ModPod))
- Scope: products `recBVDyal8VGGVEZM`, `recOu5xXheu2POoIa`, `recSYgE1Y3I11JIsr`, `recspYM9bd9APNCOO`, `recyMjzPUzBOvXD7Q`
- Atlas read: Atlas read 2026-10-20 via the Airtable connector (read-only), after the seven founder-approved edits; fields restricted to the generator's allowlists; feature definitions carry Feature Name only (the generator reads no other feature field), sha256 `11af5f405f64e441783d9b1d1c12915dba03d798ee32e58a1a3ad4de61e88515`
- Built on commit `392de7e0a5ef`; tool atlas-tools/publish-targeted-update.py
- Mode: APPLY

## Where each product is published

- `recBVDyal8VGGVEZM` — discovery-living-in-the-garden.html, garden-room-detail-alternatives-v1.json, garden-room-detail-bestfor-v1.json, garden-room-detail-considerations-v1.json, garden-room-detail-evidence-v1.json, garden-room-detail-planningconsiderations-v1.json, garden-room-detail-strengths-v1.json, garden-room-detail-typicalhomeowner-v1.json, garden-room-recommendation-universe-v1.json, search-index-v1.json
- `recOu5xXheu2POoIa` — atlas-recognition-pool.json, discovery-living-in-the-garden.html, garden-room-detail-alternatives-v1.json, garden-room-detail-bestfor-v1.json, garden-room-detail-considerations-v1.json, garden-room-detail-evidence-v1.json, garden-room-detail-planningconsiderations-v1.json, garden-room-detail-strengths-v1.json, garden-room-detail-typicalhomeowner-v1.json, garden-room-recommendation-universe-v1.json, search-index-v1.json
- `recSYgE1Y3I11JIsr` — atlas-recognition-pool.json, discovery-living-in-the-garden.html, garden-room-detail-alternatives-v1.json, garden-room-detail-bestfor-v1.json, garden-room-detail-considerations-v1.json, garden-room-detail-evidence-v1.json, garden-room-detail-planningconsiderations-v1.json, garden-room-detail-strengths-v1.json, garden-room-detail-typicalhomeowner-v1.json, garden-room-recommendation-universe-v1.json, search-index-v1.json
- `recspYM9bd9APNCOO` — atlas-recognition-pool.json, discovery-living-in-the-garden.html, garden-room-detail-alternatives-v1.json, garden-room-detail-bestfor-v1.json, garden-room-detail-considerations-v1.json, garden-room-detail-evidence-v1.json, garden-room-detail-planningconsiderations-v1.json, garden-room-detail-strengths-v1.json, garden-room-detail-typicalhomeowner-v1.json, garden-room-recommendation-universe-v1.json, search-index-v1.json
- `recyMjzPUzBOvXD7Q` — discovery-living-in-the-garden.html, garden-room-detail-alternatives-v1.json, garden-room-detail-bestfor-v1.json, garden-room-detail-considerations-v1.json, garden-room-detail-evidence-v1.json, garden-room-detail-planningconsiderations-v1.json, garden-room-detail-strengths-v1.json, garden-room-detail-typicalhomeowner-v1.json, garden-room-recommendation-universe-v1.json, search-index-v1.json

## Living in the Garden (garden rooms)

- changed `recBVDyal8VGGVEZM` The Nova 21.5m Pavillion Sun Room
    - `.features.installationModel.text`: TURNKEY INSTALLATION INCLUDED. Published ModPod range terms… → INSTALLATION AVAILABLE (OPTIONAL). Read from the product's …
    - `.features.installationModel.evidenceScope`: Range-Level → Product-Specific
    - `.priceBasisAxes.erection`: INCLUDED → EXCLUDED
    - `.priceBasisClass`: ERECTED_SERVICES_UNKNOWN → KIT_SELF_ASSEMBLY
    - `.priceEvidenceRef.basisLeadPhrase`: TURNKEY INSTALLATION INCLUDED → INSTALLATION AVAILABLE (OPTIONAL)
- **REMOVED / HELD** `recOu5xXheu2POoIa` ModPod Lira — no longer published by the generator's own rules
- **REMOVED / HELD** `recSYgE1Y3I11JIsr` ModPod Vaya — no longer published by the generator's own rules
- **REMOVED / HELD** `recspYM9bd9APNCOO` ModPod Nova — no longer published by the generator's own rules
- changed `recyMjzPUzBOvXD7Q` The Nova 17.8m Pavillion Sun Room
    - `.features.installationModel.text`: TURNKEY INSTALLATION INCLUDED. Recorded as published for th… → INSTALLATION AVAILABLE (OPTIONAL). Read from the product's …
    - `.features.installationModel.evidenceScope`: Range-Level → Product-Specific
    - `.priceBasisAxes.erection`: INCLUDED → EXCLUDED
    - `.priceBasisClass`: ERECTED_SERVICES_UNKNOWN → KIT_SELF_ASSEMBLY
    - `.priceEvidenceRef.basisLeadPhrase`: TURNKEY INSTALLATION INCLUDED → INSTALLATION AVAILABLE (OPTIONAL)

Header: eligibleCount 573 → 570; highConfidenceCount 153 → 151; withCaveatCount 420 → 419; excludedCount 9 → 12; exclusionSummaryByReason {"E": 3, "F": 1, "G": 5} → {"E": 3, "F": 1, "G": 5, "C": 3}; missingPriceCount 223 → 222; priceEvidenceSummary {"verified": 270, "present-unverified":… → {"verified": 268, "present-unverified":…; governedDigest 22e3cdbb9ed1197851bf959f99b173dfbb55c53… → 1c612c2ca3153eb4a4938345853e120743cd62c…
Detail partitions updated: alternatives, bestFor, considerations, planningConsiderations, strengths, typicalHomeowner

## Imagery

- Atlas Asset records for this organisation: 0 before, 0 now
- imagery pass:  15 product(s) now carry authorised imagery
- Every image is still decided by apply_authorised_imagery.py: live grant, scoped prefix, product link, required credit (+ photographer), link-back, medium.

## Maker Explorers, Search, homepage

- discovery-living-in-the-garden.html · gardenRooms figures {"products": 573, "makers": 64, "confirmed": 270, "noRoute": 43} → {"products": 570, "makers": 64, "confirmed": 267, "noRoute": 43}
- Search counts {"possibility": 14, "product": 700, "supplier": 64, "journey": 9} → {"possibility": 14, "product": 697, "supplier": 64, "journey": 9}
- Search universe pin re-frozen `b45a9a8499038430…` → `3da2c97699ba18cf…` (logged in governance/SEARCH-V1-CONTRACT.md)
- Homepage figures (index.html, atlas-stats.json) are the whole-Atlas census written by atlas-stats.yml, not publication counts: untouched by design.
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
- REVIEW prove-atlas-a —     PASS   the explanatory Phase 1 placements survive unchanged |     PASS   the AA-001 note names the lockup as the single brand exception |     PASS   the lockup carries no fill, border, radius or shadow |     PASS   no Atlas mark on any other page | ============================================================================ | FAILED — 2 check(s).

## Files that change

- atlas-tools/build-search-index.py
- discovery-living-in-the-garden.html
- garden-room-detail-alternatives-v1.json
- garden-room-detail-bestfor-v1.json
- garden-room-detail-considerations-v1.json
- garden-room-detail-evidence-v1.json
- garden-room-detail-index-v1.json
- garden-room-detail-planningconsiderations-v1.json
- garden-room-detail-strengths-v1.json
- garden-room-detail-typicalhomeowner-v1.json
- garden-room-recommendation-universe-v1.json
- governance/SEARCH-V1-CONTRACT.md
- search-index-v1.json
