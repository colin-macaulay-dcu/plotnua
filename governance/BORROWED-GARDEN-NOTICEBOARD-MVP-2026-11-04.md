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

## Remaining before launch

1. Privacy notice section for the noticeboard (what is shown, the private e-mail, retention), and Terms wording.
2. Create the D1 tables (apply migration 0004), create and deploy the intake Worker, set the page's `endpoint`.
3. Publishing: a `plotnua-garden-publish` pipeline script and workflow (copy of the Idea Board's), and register the page
   in the site's page registries (identity, header, premium, sitemap/noindex decision).
4. Link the noticeboard from the Discovery's chapter 05 / 06 (editorial change, founder approval).
5. Optional photographs: a Studio upload for an approved photograph (field and page rendering are in place).
6. Later, separately approved: switching on the enquiry relay (needs a mail provider and the insurance question settled).
