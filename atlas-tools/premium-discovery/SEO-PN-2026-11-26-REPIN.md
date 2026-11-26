# SEO and analytics package (PlotNua half): re-pin of the Premium Discovery snapshots (26 Nov 2026)

Founder approval: SEO and analytics package, 26 Nov 2026 (§1 analytics, §3.2 titles and descriptions, §3.4 small additions, §3.5 internal links). PlotArt (/plotart/) is a separate change.

Tool: `atlas-tools/seo-pn-repin-premium.py` (`--check` proves without writing). The transforms are declared once, in `atlas-tools/seo_pn_analytics.py` and in the tool itself:

1. **A · Analytics, every page.**
   - The Consent Mode v2 default (Basic mode, `data-cookieconsent="ignore"`) and one click listener go in immediately before `<script id="Cookiebot" …>`.
   - The listener fires `supplier_outbound_click`, `whatsapp_click` and `email_click`, only after statistics consent, with no personal data.
   - The GA4 config call gains `{ content_group: 'PlotNua' }`.
   - These are head-only changes.
2. **T · Titles and descriptions, three pinned heads only** (exact strings in the tool):
   - Living in the Garden: title and description;
   - Garden Retreat: title and description;
   - Home Exchange: title (its description is kept).

Body links added by the package are **not** snapshot changes. Each is declared where earlier additions are declared:
- `living-garden-added.json` → `guideReferences`: the Garden Saunas sentence;
- the natural-swimming guard → `ADDED_LINKS`: the Underground Swimming Pool exit.

**Text snapshots** (head stored as text):
- above-and-beyond
- the-borrowed-garden
- garden-retreat (A+T)
- home-exchange (A+T)
- living-garden (A+T)
- natural-swimming
- your-home-on-screen

For each, the tool:
1. proves that the branch base page (5225aae7) passes the guard's head checks against the stored head;
2. applies A (and T where listed);
3. edits the JSON text in place, refusing unless the result parses to exactly that change;
4. proves the working page passes the whole guard against the new snapshot.

**Hashed snapshots:**
- driveway-income
- hidden-bins
- hidden-cars
- parcel-house
- power-station

For each, the tool proves that every stored hash is the base page's. It then refuses unless the working page equals the base page plus A, and unless only hash facts change. Only the `head` hash moves.

**Not re-pinned** (fingerprinted to historical commits):
- `a-home-for-art-base.json`: its guard compares head script sources only, so A leaves it passing unchanged.
- `garden-room-prices-ireland-base.json`: its guard declares the change itself:
  - `SEO_PN_HEAD` maps the title and its Open Graph and Twitter copies;
  - G1 accepts the new builder-written description wording, whose figures G5 still proves;
  - the two new links and their wording are in `ADDED_LINKS` and `ADDED_TEXT`.

**Other pinned records moved by the same change**, each with its previous value kept or noted:
- `assets/h6/h6-record.json`: the homepage `analytics_and_consent` hash only.
- `atlas-tools/release/gridnua-launch-manifest.json`: both GridNua pages, plus the Readiness Check page hash and its scripts hash (entry in `repins`). GL4 now exempts exactly `seo_pn_analytics.FULL`, once, inside `<head>`, and two new planted faults prove the exemption is narrow.
- Title pins re-pinned with their previous value in a comment:
  - `prove-disc036-page.py` E1;
  - `prove-cluster1-garden-authority.mjs` J1;
  - `prove-cluster2-garden-retreat.mjs` J1;
  - `build-cluster2-garden-retreat.py` PRESERVE.
- Description pins re-pinned to the profile pages' own body text:
  - `build-search-index.py` G15 (Superior Pergola);
  - `build-lg-at-a-glance.py` R1 (The Pod Factory).
- `prove-matching-eligibility.py` E7 recomputes both ranges in the new description from the frozen evidence.
