# Price recheck dates — 2026-11-06

- Tool: atlas-tools/publish-price-recheck-dates.py (date-only; downstream steps from publish-targeted-update.py)
- Built on commit `a8334711f21e`
- Mode: APPLY

- Atlas read `snap-gos.json` sha256 `5f5d44b8f7c6c75c7330dfbdcb2fc6805c3e59e225703ac95b3a2b121cd9addd`
- Atlas read `snap-adman.json` sha256 `b5ac795c09fc61e82dfb477149f022666aa1babfa68d345689dc94335a877635`
- Atlas read `snap-ligp.json` sha256 `8b136c1979cf167c728a554ec3c857d70676ff6f2157c154dec4d5559cee775d`
- Atlas read `snap-gardenrooms.json` sha256 `a47b3a1c1e4b7a70b0b6a5e49ebaf1f4a689f55432ff16820cbee2df607602f0`

## Products (only `priceEvidenceRef.lastPriceCheck` moves)

| Product | Organisation | Published price | Check date | Atlas price record |
|---|---|---|---|---|
| `recKHXaApIugjOKti` Garden Office Solutions Garden Room 12.5m² | Garden Office Solutions | €19,950 | 2026-08-08 → 2026-11-06 | `recEpVTcTZO6kk5K7` |
| `recUs4gexxlfkaiUj` Garden Office Solutions Garden Room 17.6m² | Garden Office Solutions | €26,400 | 2026-08-08 → 2026-11-06 | `recvQesac9AycGKAS` |
| `reciolethPMEn50gQ` Garden Office Solutions Garden Room 25m² | Garden Office Solutions | €37,500 | 2026-08-08 → 2026-11-06 | `recrwl0GUIvzyOeeN` |
| `recUnUAWq0TWkNO5C` Garden Office Solutions Garden Room 26.4m² | Garden Office Solutions | €43,600 | 2026-08-08 → 2026-11-06 | `recjKlZbrQGzeVV0M` |
| `recagT4dAtSxxdqv4` Multiroom Garden Room 3m x 3.2m | Adman Steel Sheds | €9,995 | 2026-09-10 → 2026-11-06 | `recKTOf8hfKGLhwTG` |
| `recXi7u4Hv7tTcB80` Multiroom Garden Room 3m x 4.2m | Adman Steel Sheds | €11,250 | 2026-09-10 → 2026-11-06 | `rec6P2loZeEV7cPAj` |
| `recsgAs9snaK2MAfa` Multiroom Garden Room 3m x 5.2m | Adman Steel Sheds | €12,450 | 2026-09-10 → 2026-11-06 | `recg94q4pfCn3N2TR` |
| `recnbJjoXIbfxOgk2` Multiroom Garden Room 3m x 6.2m | Adman Steel Sheds | €13,550 | 2026-09-10 → 2026-11-06 | `reccojVfkzj53wa2k` |
| `recaGNRHjWWXqcX52` Multiroom Garden Room 3m x 9.2m | Adman Steel Sheds | €17,550 | 2026-09-10 → 2026-11-06 | `rec7wR2DD2cGONHzz` |
| `recA0HnNkzltWWhzi` Multiroom Garden Room 4m x 4.2m | Adman Steel Sheds | €13,150 | 2026-09-10 → 2026-11-06 | `recAjEhfW4xYiT4Uh` |
| `rechMRoBym2H90To9` Multiroom Garden Room 4m x 5.2m | Adman Steel Sheds | €14,450 | 2026-09-10 → 2026-11-06 | `recZH0JPBWdDRSnId` |
| `recWPmFXg8981XQtw` Multiroom Garden Room 4m x 6.2m | Adman Steel Sheds | €15,995 | 2026-09-10 → 2026-11-06 | `rec36RNag5A31wWKj` |
| `recUpbnPlPJO7N2wa` Multiroom Garden Room 4m x 9.2m | Adman Steel Sheds | €19,995 | 2026-09-10 → 2026-11-06 | `rec1WQ2jDFIHQnmvu` |
| `recrfXlRTCNCf8VB5` Studio Living Pod | Live in Garden Pods | €39,950 | 2026-08-13 → 2026-11-06 | `recfCtIRHKVIRKP2p` |
| `recfFcnNP9ZV4BcVW` CUBE Garden Room Range | Garden Rooms | €36,500 | 2026-10-06 → 2026-11-06 | `recmhqpPfdjlXEia2` |
| `recnBe46LKTCzLJ3P` Ultimate Garden Room Range | Garden Rooms | €43,650 | 2026-10-06 → 2026-11-06 | `recPZnwHVecuaGX88` |

Search universe pin re-frozen `c4713085a4359c8f…` → `565971774b00f418…`

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
