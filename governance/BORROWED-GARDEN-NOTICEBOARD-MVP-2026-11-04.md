# The Borrowed Garden · two-sided noticeboard MVP (private preview)

Founder decision, 4 November 2026: build the original two-sided noticeboard on the PlotArt Studio architecture. This
replaces the earlier direction to develop the Airtable registers into a matching service. Private preview only: nothing
deployed, no migration applied, no Worker created, nothing published.

Branch: `preview/borrowed-garden-board` (not released; GitHub Pages serves `main` only).

## What was built (reusing the Idea Board pattern)

| Part | File | State |
|---|---|---|
| Public intake Worker (`plotnua-garden-board`) | `worker/plotart-studio/src/garden.js`, `wrangler.garden.toml` | Ships closed: `GARDEN_ENABLED = "false"` |
| Shared rules (closed lists, no contact details or addresses) | `worker/plotart-studio/src/garden-rules.js` | |
| D1 tables (listings, daily cap, relay records) | `migrations/0004_garden_board.sql`, `schema.sql` | Not applied anywhere |
| Founder moderation (Garden tab: approve, reject, remove, expire, tidy, delete) | `src/index.js`, `ui/admin.js`, `build-assets.mjs` | Inside the existing Studio (Cloudflare Access) |
| Pipeline endpoint (public fields only) | `GET /api/pipeline/garden` | Existing pipeline token |
| Public page builder (`borrowed-garden-board.html`) | `atlas-tools/build-garden-board.py`, `atlas-tools/garden-board/` | Not built into the site; `endpoint: null` = no form |
| Enquiry relay route | `src/enquiry.js` `/v1/garden-enquiry`, `wrangler.enquiry.toml` | Prepared, OFF: `GARDEN_ENQUIRIES_ENABLED = "false"` |
| Proof | `worker/plotart-studio/test/prove-garden-board.mjs` | 66 checks, PASS |

Listing fields: kind (I have space / I want space), county, general area, type of space, approximate availability,
short description, optional approved photograph (`photo_key`), reference, date posted, status, expiry. Private: the
contact e-mail (founder only; never published), consent time. No name, phone, address, Eircode or IP is stored.

Unused monetisation fields: `account_type` (individual), `listing_tier` (free), `featured_until`, `expires_at`,
`organisation_id`. No code path sets them; the database refuses unknown values; the page orders by date only.

## Existing registers

Airtable records untouched. Not migrated (consent was for a private register). Both check-page builders now refuse to
run while registrations are paused (`build-g6-open-register.py`, `build-grower-register.py`); the grower builder no
longer writes the Discovery at all (in its open mode it overwrote `discovery-the-borrowed-garden.html`).

## Register Worker configuration review (deploy effect on stored Airtable settings)

`worker/garden-register/wrangler.toml` on `main` sets `WRITES_ENABLED` and `GROWER_WRITES_ENABLED` to `"false"`.
`AIRTABLE_BASE` is a var set at deploy time, not in the file. A plain `wrangler deploy` deletes every var not in the
file, so it would remove `AIRTABLE_BASE`. Secrets (`AIRTABLE_TOKEN`) are never deleted by a deploy.

Recommended pause deploy (founder's machine, Cloudflare login): `cd worker/garden-register && npx wrangler deploy --keep-vars`.
Both write switches go off; `AIRTABLE_BASE` and the token stay as they are; no record is read, changed or deleted.

## Release candidate (4 Nov 2026, later the same day)

Added on the same branch: the "Post a listing — Free" button and four status points (free, reviewed, no contact yet,
no arrangements); the empty-board invitation; Privacy Notice V10 (atlas-tools/privacy_v10_layer.py, applied to
privacy.html, exact and reversible on V9; Section 7 also notes that new registrations are paused) and a Terms
sub-section (Section 10); the publisher (atlas-tools/plotnua-garden-publish.py) and its workflow
(.github/workflows/plotnua-garden-publish.yml), OFF until flags.json garden_publish_enabled is true; Studio starts a
publish on approve / save / remove / expire; the page registered in the identity, header and Premium registries; the
Discovery's chapter 05 noticeboard card and chapter 06 route A link (DISC-025 guard declarations updated); a gate step
(build-garden-board.py --check, prove-privacy-v10.py). Proof: 77 checks.

Demonstration listings exist only in local test databases: the committed snapshot is empty, the publisher refuses to
push from a local Studio, and --simulate never pushes.

## Launch steps (founder)

1. Approve the Privacy V10 and Terms wording (they publish with the release).
2. Create the D1 tables (`wrangler d1 execute plotart-studio --remote --file migrations/0004_garden_board.sql`).
3. Deploy the intake Worker from `wrangler.garden.toml`, then set `GARDEN_ENABLED = "true"`; set
   `atlas-tools/garden-board/config.json` endpoint to its `/v1/garden-listings` address and rebuild the page.
4. Deploy the Studio (Garden tab and pipeline endpoint) through the existing studio-deploy workflow.
5. Release the branch through the governed release; set `garden_publish_enabled` to true in flags.json.
6. Separately: the register Worker pause (`npx wrangler deploy --keep-vars` in worker/garden-register).

## Still later, separately approved

Optional photographs (Studio upload); the enquiry relay (mail provider, insurance question); any paid feature.

## Production launch (founder decision 4 Nov 2026, approved for production release)

- Stage 1, backend only: b2cad2a on main. Migration 0004 was applied through studio-d1-migration.yml (run 41917513910), and only the four garden tables changed. The Studio, with the Garden tab, was deployed through studio-deploy.yml (run 41918094827). The intake Worker `plotnua-garden-board` was deployed OPEN through plotnua-garden-deploy.yml (run 41918794516), and its outside checks passed: GET 405, other origin 403, invalid listing 400. Each Cloudflare step was approved by the founder in GitHub.
- Stage 2, public: this release. The noticeboard page has the form pointed at the live endpoint, and the Discovery ch05 and ch06 links are live. It also releases Privacy V10 and the Terms section, and sets `garden_publish_enabled: true`. The board starts with no listings.
- Still off: the enquiry relay (`GARDEN_ENQUIRIES_ENABLED = "false"`), matching, introductions, payments and paid prominence.
- Note: studio-d1-migration.yml classifies every migration against a temporary file name. Because that name has no migration number, an additive migration is still routed to `studio-database`, so it needs the founder's approval. The migration was correct, but that classification is a known limitation.
