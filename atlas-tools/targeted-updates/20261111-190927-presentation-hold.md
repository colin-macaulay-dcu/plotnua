# Price-presentation hold

- Tool: atlas-tools/publish-presentation-hold.py (hold-only; downstream steps from publish-targeted-update.py)
- Built on commit `b80c2bd1650e`
- Register: atlas-tools/price-presentation-holds.json
- Mode: APPLY

## Products (only priceSafeForMatching, priceBasisConfidence and priceEvidence.presentationHold move)

| Product | Organisation | Safe for matching | Basis confidence |
|---|---|---|---|
| `recKHXaApIugjOKti` Garden Office Solutions Garden Room 12.5m² | Garden Office Solutions | True → False | EXPLICIT → UNSAFE |
| `recUs4gexxlfkaiUj` Garden Office Solutions Garden Room 17.6m² | Garden Office Solutions | True → False | EXPLICIT → UNSAFE |
| `reciolethPMEn50gQ` Garden Office Solutions Garden Room 25m² | Garden Office Solutions | True → False | EXPLICIT → UNSAFE |
| `recUnUAWq0TWkNO5C` Garden Office Solutions Garden Room 26.4m² | Garden Office Solutions | True → False | EXPLICIT → UNSAFE |
| `recBVDyal8VGGVEZM` The Nova 21.5m Pavillion Sun Room | Outdoor Living (ModPod) | True → False | EXPLICIT → UNSAFE |
| `reczxM0lggLXTBCdU` Garden Room PSML2 | Lugarde | True → False | NOT_CONFIRMED → UNSAFE |

Search universe pin re-frozen `f6e10315b4c3d005…` → `1f31730f57412157…`

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
- garden-room-recommendation-universe-v1.json
- governance/SEARCH-V1-CONTRACT.md
- search-index-v1.json
