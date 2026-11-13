# Targeted publication — Modern Garden Rooms

- Organisation: `recZcfloN72CBES6I` (Modern Garden Rooms)
- Scope: products `rec8yqq3yj2qFyU7T`, `recBW2vBPcT0kOT1o`, `recGMPCzZKWL0MO10`, `recQhafVxkW46trn6`, `recSpzyQeSlo8yylE`
- Atlas read: ATLAS READ-BACK — scoped read of Atlas Core appoLZFWesvoPhZGR, 13 Nov 2026, after the founder-approved Modern Garden Rooms writes (incl. the 11:55 Guest Room planning correction). Products, pricing and organisation: fresh Airtable-connector reads (read-only) taken after the writes. Feature values: the 13 Nov pre-write connector backup with the 36 approved updates applied (server-side filter confirmed exactly these 36 now carry the 13 Nov text); availability and feature definitions unchanged since the 11 Oct complete snapshot (availability re-read 13 Nov, identical). Converted to the REST shape by build_mgr_snapshot.py; values copied unaltered., sha256 `43293cb11735dbbc699d7f8d2b43ac186918b32eb481cfe78517078ace8f9e96`
- Built on commit `e3d69644f455`; tool atlas-tools/publish-targeted-update.py
- Mode: APPLY

## Where each product is published

- `rec8yqq3yj2qFyU7T` — atlas-recognition-pool.json, discovery-living-in-the-garden.html, garden-room-detail-alternatives-v1.json, garden-room-detail-bestfor-v1.json, garden-room-detail-considerations-v1.json, garden-room-detail-evidence-v1.json, garden-room-detail-planningconsiderations-v1.json, garden-room-detail-sources-v1.json, garden-room-detail-strengths-v1.json, garden-room-detail-typicalhomeowner-v1.json, garden-room-recommendation-universe-v1.json, search-index-v1.json
- `recBW2vBPcT0kOT1o` — atlas-recognition-pool.json, discovery-living-in-the-garden.html, garden-room-detail-alternatives-v1.json, garden-room-detail-bestfor-v1.json, garden-room-detail-considerations-v1.json, garden-room-detail-evidence-v1.json, garden-room-detail-planningconsiderations-v1.json, garden-room-detail-sources-v1.json, garden-room-detail-strengths-v1.json, garden-room-detail-typicalhomeowner-v1.json, garden-room-recommendation-universe-v1.json, search-index-v1.json
- `recGMPCzZKWL0MO10` — atlas-recognition-pool.json, discovery-living-in-the-garden.html, garden-room-detail-alternatives-v1.json, garden-room-detail-bestfor-v1.json, garden-room-detail-considerations-v1.json, garden-room-detail-evidence-v1.json, garden-room-detail-planningconsiderations-v1.json, garden-room-detail-sources-v1.json, garden-room-detail-strengths-v1.json, garden-room-detail-typicalhomeowner-v1.json, garden-room-recommendation-universe-v1.json, search-index-v1.json
- `recQhafVxkW46trn6` — atlas-recognition-pool.json, discovery-living-in-the-garden.html, garden-room-detail-alternatives-v1.json, garden-room-detail-bestfor-v1.json, garden-room-detail-considerations-v1.json, garden-room-detail-evidence-v1.json, garden-room-detail-planningconsiderations-v1.json, garden-room-detail-sources-v1.json, garden-room-detail-strengths-v1.json, garden-room-detail-typicalhomeowner-v1.json, garden-room-recommendation-universe-v1.json, search-index-v1.json
- `recSpzyQeSlo8yylE` — atlas-recognition-pool.json, discovery-living-in-the-garden.html, garden-room-detail-alternatives-v1.json, garden-room-detail-bestfor-v1.json, garden-room-detail-considerations-v1.json, garden-room-detail-evidence-v1.json, garden-room-detail-planningconsiderations-v1.json, garden-room-detail-sources-v1.json, garden-room-detail-strengths-v1.json, garden-room-detail-typicalhomeowner-v1.json, garden-room-recommendation-universe-v1.json, search-index-v1.json

## Living in the Garden (garden rooms)

- unchanged `rec8yqq3yj2qFyU7T` Modern Golf Simulator Room
- unchanged `recBW2vBPcT0kOT1o` Modern Garden Guest Room
- unchanged `recGMPCzZKWL0MO10` Modern Modular Garden Room
- unchanged `recQhafVxkW46trn6` Modern Garden Gym
- unchanged `recSpzyQeSlo8yylE` Modern Garden Office

Header: unchanged
Detail partitions updated: planningConsiderations

## Imagery

- snapshot carries no Asset records; approved-image-assets-v1.json unchanged
- imagery pass:  15 product(s) now carry authorised imagery
- Every image is still decided by apply_authorised_imagery.py: live grant, scoped prefix, product link, required credit (+ photographer), link-back, medium.

## Maker Explorers, Search, homepage

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
- OK prove-atlas-a

## Files that change

- garden-room-detail-evidence-v1.json
- garden-room-detail-index-v1.json
- garden-room-detail-planningconsiderations-v1.json
