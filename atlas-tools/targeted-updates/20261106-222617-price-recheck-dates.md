# Price recheck dates — 2026-11-06

- Tool: atlas-tools/publish-price-recheck-dates.py (date-only; downstream steps from publish-targeted-update.py)
- Built on commit `3ff9c9784e7f`
- Mode: APPLY

- Atlas read `READBACK-hansa24-five-2026-11-06.json` sha256 `08f7bc0b8d88579b6668578c896b030eac96fda40269892d32385c3a5c6edd33`

## Products (only `priceEvidenceRef.lastPriceCheck` moves)

| Product | Organisation | Published price | Check date | Atlas price record |
|---|---|---|---|---|
| `rec9uQSpCV1OnrV9y` Contemporary Garden Office Olivia ALU | Hansa24 Group | €8,870 | 2026-08-27 → 2026-11-06 | `rec7N63XObCPQYHzS` |
| `recEZ2nnKMBzuHnQ6` Contemporary Garden Office Pod Olivia | Hansa24 Group | €6,630 | 2026-08-27 → 2026-11-06 | `recq7Rl2SC6CqKORb` |
| `rechyfJmxqpq0gXar` Contemporary Garden Room Aurora | Hansa24 Group | €10,600 | 2026-08-27 → 2026-11-06 | `recrXjXLBCZhNlOJu` |
| `recClI0ZejdwUFLQc` Contemporary Garden Room Leo | Hansa24 Group | €8,570 | 2026-08-27 → 2026-11-06 | `rec0yjDgfeISpEki5` |
| `recjtDoDYtp7TKCze` Garden Snooker Room Hansa B | Hansa24 Group | €15,680 | 2026-08-27 → 2026-11-06 | `recQaXsKXHkrBpHne` |

Search universe pin re-frozen `030338cbe12d237a…` → `238b26cbf2f56be9…`

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
- garden-room-recommendation-universe-v1.json
- governance/SEARCH-V1-CONTRACT.md
- search-index-v1.json
