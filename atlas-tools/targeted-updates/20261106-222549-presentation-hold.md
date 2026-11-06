# Price-presentation hold

- Tool: atlas-tools/publish-presentation-hold.py (hold-only; downstream steps from publish-targeted-update.py)
- Built on commit `39e707808f80`
- Register: atlas-tools/price-presentation-holds.json
- Mode: APPLY

## Products (only priceSafeForMatching, priceBasisConfidence and priceEvidence.presentationHold move)

| Product | Organisation | Safe for matching | Basis confidence |
|---|---|---|---|
| `recDIcUb7S6pP8JCx` Rayco Modular Homes Garden Room (entry range) | Rayco Modular Homes | True → False | EXPLICIT → UNSAFE |

Search universe pin re-frozen `1be874ad227c76a2…` → `030338cbe12d237a…`

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
