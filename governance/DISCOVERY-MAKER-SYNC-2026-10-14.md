# Discovery maker synchronisation — audit and build record

**Date:** 14 October 2026  
**Brief:** "Automatic Discovery Maker Synchronisation · permanent platform capability"  
**Status:** built and tested locally. Not pushed, not deployed, no schedule enabled, no full Atlas refresh run, no supplier contacted.

## 1. What already existed (reused, unchanged)

| Layer | Component | Automatic today? |
|---|---|---|
| Atlas → universe | `.github/scripts/generate_garden_room_universe.py`, `generate_additional_home_universe.py`, `generate_wellness_universe.py` (one Atlas Product Category each) | Yes, by generator. The daily refresh workflow is **paused** (since 22 Sep 2026). |
| One supplier at a time | `atlas-tools/publish-targeted-update.py` | Yes: dry run, change report, apply, validation. Rebuilds explorers and Search itself. |
| Eligibility | Qualification, holds, the publication gate (`publicVisibility`, fail-closed), image-rights records, the public-information register (refuses objections) | Yes, upstream of every page. |
| Maker Explorer | `build-maker-explorer.py` + shared `maker-explorer.js/.css`; per-Discovery `PAGES` config; counts derived from universes (guard G1) | Yes, on rebuild. Two pages: Living in the Garden, Garden Retreat. |
| Provider explorers | Borrowed Garden, House as Power Station (organisations only, no products) | Yes, own builders and checks. |
| Search | `build-search-index.py`, reading the same three universes | Yes, on rebuild. |
| Homepage totals | `.github/scripts/atlas_stats.py`, daily workflow (active) | Yes. Atlas-wide counts, not Discovery counts. |

**Conclusion:** the pipeline from universe to page was already automatic, and counts were already derived, never typed. What was missing was a Discovery-level registry tied to Atlas categories, a publication snapshot with a reviewable diff, targeted regeneration with a boundary check, and cross-checks proving the explorers and Search agree.

## 2. Findings

1. **Atlas coverage.** Read-only read-back, 14 Oct 2026: 1,242 products in 14 Product Category values. Only three categories have a publication route: Garden Rooms (575), Wellness / Sauna (153) and Additional Home (140). **374 products in 11 categories have no generator, no eligibility rule and no Discovery**: Garages 101, Timber Sheds 63, Homes 39, Steel Sheds 39, Log Cabins 31, Carports 30, Garden Storage 22, Summerhouses 21, Greenhouses 11, Guest Accommodation 6, Treehouses 3. A further 8 products have no category.
2. **Atlas's own Discovery registry is unused.** Atlas has a Discoveries table, linked to Categories and Products, but it holds one populated record (DISC-025) and three blank rows. No product is linked to a Discovery.
3. **Explorer and Search diverge by design on garden homes.** The Living in the Garden explorer lists 28 garden homes; Search lists 11. Search withholds 17 because their makers already have a Garden Room supplier record (Search rule R3), so the supplier corpus is not re-aggregated. This is documented, not a leak; it is recognised as a declared exception and never widened.
4. **Garden Retreat counts.** The tabs sum to 125, but there are 120 distinct products: five dual-use products appear in two tabs. Per-tab counts are correct, and no total is shown on the page.
5. **Search `--check` does not detect a stale index,** and `--apply` stamps a new time and commit on every run. The sync layer therefore judges Search by its records and keeps the committed bytes when no record changed.

## 3. What was built

- **`atlas-tools/sync-discovery-makers.py`**
  - **Registry:** Discovery ID (Search's existing `poss-…` IDs), route, Atlas categories, explorer type and Search eligibility. Tab configuration is not copied: guard S1 proves the registry and the Maker Explorer's `PAGES` agree. The 11 unrouted categories are declared, never guessed.
  - **State:** derived only through the Maker Explorer's own source readers. Each product appears once, with every Discovery and tab it is listed in. Counts are deduplicated.
  - **Change report:** compared with `atlas-tools/discovery-maker-snapshot-v1.json`. It lists new makers, new, updated and removed products, newly held products, placement changes, price changes, image-rights changes, count changes and changed universes.
  - **Modes:**
    - `--report`: dry run;
    - `--check`: fails if anything is pending;
    - `--apply --discovery <id>`: targeted;
    - `--apply --all`: full, founder-approved;
    - `--apply --baseline`: records the snapshot only.
  - **Targeted apply refuses** when another Discovery has pending changes, because Search is site-wide.
  - **Verification S1–S7:**
    - registry and categories;
    - category integrity, so a mismatch is held, never published;
    - pages up to date;
    - provider explorers;
    - Search parity;
    - no held product anywhere public;
    - every product link resolves or is VERIFIED.
- **`atlas-tools/discovery-maker-snapshot-v1.json`:** the baseline, recorded from the current published site: 720 products across 4 Discoveries. Nothing else was written.
- **`atlas-tools/test-sync-discovery-makers.py`:** 29 tests, each in a throwaway clone.

## 4. Founder decisions outstanding

1. **The 11 unrouted Atlas categories (374 products).** Each needs its own eligibility rule, a generator or an extension of one, and a Discovery to live in, before anything in it can be public. This is a publication-policy decision, not a sync change.
2. **Garden homes in Search (17 withheld under R3).** Keep the exception, or approve extending the Search supplier corpus so all 28 are searchable.
3. **Atlas Discoveries table.** Populate it and link Products and Categories, so the registry can be read from Atlas, or keep the registry in code, as now.
4. **Hook into targeted publication.** After `publish-targeted-update.py`, run `sync-discovery-makers.py --report`, then `--apply --discovery <id>`. Wiring that in automatically is a change to the publication tool and needs approval.
5. **Scheduled use.** The tool supports a scheduled `--check` (alert only). Enabling any schedule, or resuming the paused universe refresh, needs separate approval.
