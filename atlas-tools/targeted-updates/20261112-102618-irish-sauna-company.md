# Targeted publication — Irish Sauna Company

- Organisation: `recLW0vZbkBGPRkZ9` (Irish Sauna Company)
- Scope: products `recQszPvHe5Cu7wY5`, `recTBQcdOO0yoULqN`, `reccdnuccLgq8dlqh`, `rect8UKFyZodW593p`
- Atlas read: PROPOSED SNAPSHOT — NOT AN ATLAS READ-BACK. Built 12 Nov 2026 from a read-only Atlas read (Airtable connector, same day) of Irish Sauna Company ORG-000226 (4 Island Collection products, 4 pricing records) with the proposed writes ISC-1 to ISC-4 of atlas-tools/proposed-atlas-updates/2026-11-12-wellness-isc-pineca.json applied in memory. For local generation and validation only; Atlas itself is unchanged. Must be replaced by a genuine scoped read-back after the approved Atlas writes, before any production release., sha256 `bb828b7be7c18c50ac7081183ddb470749f7ab9b69676935df4e2ed1a4986dbc`
- Built on commit `983eac2e5322`; tool atlas-tools/publish-targeted-update.py
- Mode: APPLY

## Where each product is published

- `recQszPvHe5Cu7wY5` — discovery-garden-retreat.html, search-index-v1.json, wellness-universe-v1.json
- `recTBQcdOO0yoULqN` — discovery-garden-retreat.html, search-index-v1.json, wellness-universe-v1.json
- `reccdnuccLgq8dlqh` — discovery-garden-retreat.html, search-index-v1.json, wellness-universe-v1.json
- `rect8UKFyZodW593p` — discovery-garden-retreat.html, search-index-v1.json, wellness-universe-v1.json

## Garden Retreat (wellness)

- **STATE** `recQszPvHe5Cu7wY5` The Aran | 4–6 Person Luxury Garden Sauna: ELIGIBLE/PUBLISHABLE → HELD/PUBLISHABLE (public)
- changed `recQszPvHe5Cu7wY5` The Aran | 4–6 Person Luxury Garden Sauna
    - `.productUrl`: https://irishsaunacompany.com/products/the-aran-4-6-person-… → null
    - `.price.state`: VERIFIED_NUMERIC_PRICE → PRICE_NOT_ESTABLISHED
    - `.price.amount`: 11500 → <absent>
    - `.price.currency`: EUR → <absent>
    - `.price.type`: Sale Price → <absent>
    - `.price.basis`: Published sale price, including VAT. → <absent>
    - `.qualification.state`: ELIGIBLE → HELD
    - `.qualification.heldReasons`: [] → ["evidence-incomplete"]
    - `.listingBasis`: SUPPLIER_PERMISSION → null
- unchanged `recTBQcdOO0yoULqN` The Clare | 1–2 Person Garden Sauna
- **STATE** `reccdnuccLgq8dlqh` The Skellig | Luxury 6–8 Person Garden Sauna: ELIGIBLE/PUBLISHABLE → HELD/PUBLISHABLE (public)
- changed `reccdnuccLgq8dlqh` The Skellig | Luxury 6–8 Person Garden Sauna
    - `.productUrl`: https://irishsaunacompany.com/products/the-skellig-luxury-8… → null
    - `.price.state`: VERIFIED_NUMERIC_PRICE → PRICE_NOT_ESTABLISHED
    - `.price.amount`: 19600 → <absent>
    - `.price.currency`: EUR → <absent>
    - `.price.type`: Sale Price → <absent>
    - `.price.basis`: Published sale price, including VAT. → <absent>
    - `.qualification.state`: ELIGIBLE → HELD
    - `.qualification.heldReasons`: [] → ["evidence-incomplete"]
    - `.listingBasis`: SUPPLIER_PERMISSION → null
- changed `rect8UKFyZodW593p` The Inis Mor | 2–4 Person Garden Sauna
    - `.productName`: The Inis | 2–4 Person Garden Sauna → The Inis Mor | 2–4 Person Garden Sauna
    - `.productUrl`: https://irishsaunacompany.com/products/the-inis-2-4-person-… → https://irishsaunacompany.com/products/the-inis-mor-2-4-per…

Header: snapshotScope Atlas Core appoLZFWesvoPhZGR via the Ai… → Atlas Core appoLZFWesvoPhZGR via the Ai…; eligibleCount 135 → 133; kindCounts {"sauna": 100, "hot-tub": 24, "cold-plu… → {"sauna": 98, "hot-tub": 24, "cold-plun…; heldCount 30 → 32; listingBasisCounts {"SUPPLIER_PERMISSION": 50, "PUBLIC_INF… → {"SUPPLIER_PERMISSION": 48, "PUBLIC_INF…

## Imagery

- snapshot carries no Asset records; approved-image-assets-v1.json unchanged
- imagery pass:  15 product(s) now carry authorised imagery
- Every image is still decided by apply_authorised_imagery.py: live grant, scoped prefix, product link, required credit (+ photographer), link-back, medium.

## Maker Explorers, Search, homepage

- discovery-garden-retreat.html · saunas figures {"products": 100, "makers": 8, "confirmed": 0, "noRoute": 0} → {"products": 98, "makers": 8, "confirmed": 0, "noRoute": 0}
- Search counts {"possibility": 38, "product": 722, "supplier": 65, "journey": 9} → {"possibility": 38, "product": 720, "supplier": 65, "journey": 9}
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
- OK test_wellness_universe
- OK prove-atlas-a

## Files that change

- discovery-garden-retreat.html
- search-index-v1.json
- wellness-universe-v1.json
