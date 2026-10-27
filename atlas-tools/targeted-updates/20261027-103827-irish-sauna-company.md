# Targeted publication — Irish Sauna Company

- Organisation: `recLW0vZbkBGPRkZ9` (Irish Sauna Company)
- Scope: products `recJlhoNav6YNU1zj`, `recQszPvHe5Cu7wY5`, `recRgVJcPwTtY1ikY`, `recSYzKR0BjBrdYMQ`, `recTBQcdOO0yoULqN`, `reccdnuccLgq8dlqh`, `rect8UKFyZodW593p`
- Atlas read: {'description': 'Read-only scoped Atlas export for the Irish Sauna Company Island Collection replacement (founder approval 27 Oct 2026, run ISC-COLLECTION-2026-10-27), read back through the Airtable connector immediately after the supervised writes. Products, pricing and availability carry the fields the wellness generator and the targeted publisher read; feature values, features and assets are deliberately omitted (the wellness universe reads none of them, and wellness imagery is enumerated in image-rights-records.json, not approved-image-assets-v1.json).', 'checked': '2026-10-27'}, sha256 `7442073f692e12dbd7376d76adf3037f7ab1453a850f3d05e0fe6c40de63aeed`
- Built on commit `a016feef9d24`; tool atlas-tools/publish-targeted-update.py
- Mode: APPLY

## Where each product is published

- `recJlhoNav6YNU1zj` — wellness-universe-v1.json
- `recQszPvHe5Cu7wY5` — not published
- `recRgVJcPwTtY1ikY` — discovery-garden-retreat.html, search-index-v1.json, wellness-universe-v1.json
- `recSYzKR0BjBrdYMQ` — discovery-garden-retreat.html, search-index-v1.json, wellness-universe-v1.json
- `recTBQcdOO0yoULqN` — not published
- `reccdnuccLgq8dlqh` — not published
- `rect8UKFyZodW593p` — not published

## Garden Retreat (wellness)

- unchanged `recJlhoNav6YNU1zj` Harvia Legend Wood-Burning Outdoor Sauna (supplied by Irish Sauna Company)
- **NEW** `recQszPvHe5Cu7wY5` The Aran | 4–6 Person Luxury Garden Sauna
- **STATE** `recRgVJcPwTtY1ikY` Harvia Alpina View Large Outdoor Sauna (supplied by Irish Sauna Company): ELIGIBLE/PUBLISHABLE → HELD/PUBLISHABLE (public)
- changed `recRgVJcPwTtY1ikY` Harvia Alpina View Large Outdoor Sauna (supplied by Irish Sauna Company)
    - `.productUrl`: https://irishsaunacompany.com/products/harvia-alpina-view-l… → null
    - `.price.state`: VERIFIED_NUMERIC_PRICE → PRICE_NOT_ESTABLISHED
    - `.price.amount`: 27978 → <absent>
    - `.price.currency`: EUR → <absent>
    - `.price.type`: Standard Price → <absent>
    - `.price.basis`: Published price, including VAT. → <absent>
    - `.qualification.state`: ELIGIBLE → HELD
    - `.qualification.heldReasons`: [] → ["evidence-incomplete"]
    - `.listingBasis`: SUPPLIER_PERMISSION → null
- **STATE** `recSYzKR0BjBrdYMQ` Harvia Legend Electric Outdoor Sauna (supplied by Irish Sauna Company): ELIGIBLE/PUBLISHABLE → HELD/PUBLISHABLE (public)
- changed `recSYzKR0BjBrdYMQ` Harvia Legend Electric Outdoor Sauna (supplied by Irish Sauna Company)
    - `.productUrl`: https://irishsaunacompany.com/products/harvia-legend-electr… → null
    - `.price.state`: VERIFIED_NUMERIC_PRICE → PRICE_NOT_ESTABLISHED
    - `.price.amount`: 17880 → <absent>
    - `.price.currency`: EUR → <absent>
    - `.price.type`: Standard Price → <absent>
    - `.price.basis`: Published price, including VAT. → <absent>
    - `.qualification.state`: ELIGIBLE → HELD
    - `.qualification.heldReasons`: [] → ["evidence-incomplete"]
    - `.listingBasis`: SUPPLIER_PERMISSION → null
- **NEW** `recTBQcdOO0yoULqN` The Clare | 1–2 Person Garden Sauna
- **NEW** `reccdnuccLgq8dlqh` The Skellig | Luxury 6–8 Person Garden Sauna
- **NEW** `rect8UKFyZodW593p` The Inis | 2–4 Person Garden Sauna

Header: snapshotScope Atlas Core appoLZFWesvoPhZGR via the Ai… → Atlas Core appoLZFWesvoPhZGR via the Ai…; sourceCategoryCount 154 → 158; eligibleCount 120 → 122; kindCounts {"sauna": 91, "hot-tub": 22, "cold-plun… → {"sauna": 93, "hot-tub": 22, "cold-plun…; heldCount 22 → 24; listingBasisCounts {"SUPPLIER_PERMISSION": 35, "PUBLIC_INF… → {"SUPPLIER_PERMISSION": 37, "PUBLIC_INF…

## Imagery

- snapshot carries no Asset records; approved-image-assets-v1.json unchanged
- imagery pass:  15 product(s) now carry authorised imagery
- Every image is still decided by apply_authorised_imagery.py: live grant, scoped prefix, product link, required credit (+ photographer), link-back, medium.

## Maker Explorers, Search, homepage

- discovery-garden-retreat.html · saunas figures {"products": 91, "makers": 6, "confirmed": 0, "noRoute": 0} → {"products": 93, "makers": 6, "confirmed": 0, "noRoute": 0}
- Search counts {"possibility": 18, "product": 697, "supplier": 64, "journey": 9} → {"possibility": 18, "product": 699, "supplier": 64, "journey": 9}
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
- REVIEW test_wellness_universe — ::error::public-information register row for 'Brand New Saunas Ltd' is malformed | Nothing was written. | ::error::public-information register row for 'Brand New Saunas Ltd' is malformed | Nothing was written. | ::error::price-currency-corrections: recFAKE000000001 Atlas price 1200 Standard Price no longer matches the evidenced 1000 Standard Price; review the register | Nothing was written.
- OK prove-atlas-a

## Files that change

- discovery-garden-retreat.html
- search-index-v1.json
- wellness-universe-v1.json
