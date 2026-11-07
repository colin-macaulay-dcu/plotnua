# Price-presentation hold

- Tool: atlas-tools/publish-presentation-hold.py (hold-only; downstream steps from publish-targeted-update.py)
- Built on commit `651a154` plus the register entry (a local preparation commit `53e52dc` that was folded into this release commit)
- Register: atlas-tools/price-presentation-holds.json
- Mode: APPLY

## Products (only priceSafeForMatching, priceBasisConfidence and priceEvidence.presentationHold move)

| Product | Organisation | Safe for matching | Basis confidence |
|---|---|---|---|
| `recej5DFaBD76ODlv` Garden Room PREMIUM S Insulated PLUS — 10 m² (4.1 × 2.4 m) | Pineca Ireland | True → False | NO_BASIS_STATED → UNSAFE |

Search universe pin re-frozen `7eef16c3621630dd…` → `33ea49448343e8a9…`

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
