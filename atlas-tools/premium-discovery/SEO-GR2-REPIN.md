# SEO-GR2 re-pin of the Premium Discovery base snapshots (8 Nov 2026)

Founder approval: Stage SEO-GR2, technical SEO corrections (8 Nov 2026).

Tool: `atlas-tools/seo-gr2-repin-premium-bases.py`. It applies exactly two declared transforms to the pinned snapshots, and nothing else:

1. **Homepage links.** An `href` that resolves to the site-root `/index.html` becomes `/`, keeping any `#fragment`. It uses the same resolver as `atlas-tools/seo-gr2-home-links.py`, which made the identical change on the live pages.
2. **Living in the Garden only.** The WebPage `dateModified` changes from `2026-10-26` to `2026-11-07`, the page's last content change (commit `0351c89`). `sitemap.xml` `lastmod` carries the same date.

The tool edits the JSON text in place, so formatting is unchanged. It refuses unless the edited file parses to exactly the semantic transform of the original.

| Snapshot | Changes |
|---|---|
| above-and-beyond-base.json | 3 |
| the-borrowed-garden-base.json | 4 |
| garden-retreat-base.json | 4 |
| home-exchange-base.json | 4 |
| living-garden-base.json | 2 (1 link, 1 date) |
| natural-swimming-base.json | 2 |
| your-home-on-screen-base.json | 4 |

**Hashed snapshots.** These guards pin SHA-256 hashes of page regions, not text:
- driveway-income
- hidden-bins
- hidden-cars
- parcel-house
- power-station

For each, the tool first proves that the stored `pre_main` and `post_main` hashes are those of the production page at git HEAD (8352710). It then applies the homepage-link transform to that page and stores the new hashes. It refuses if any other pinned field would change. The `head` hashes and JSON-LD are unchanged.

**Not re-pinned.** These two snapshots are fingerprinted against historical commits, so they are left as they are. Each guard instead declares the SEO-GR2 homepage mapping (`index.html[#x]` → `/[#x]`) in its link comparison (`seo_gr2_home()`), and relaxes nothing else:
- `a-home-for-art-base.json` (P0, git 0cb456d);
- `garden-room-prices-ireland-base.json` (G0).
