-- PlotArt Studio · migration 0024 · Spaces: the final gallery identifier (development 25 Nov 2026)
-- PROPOSAL FOR FOUNDER APPROVAL. NOT RUN against any real database.
-- Final curatorial identity agreed by the founder on 25 Nov 2026: Environment becomes Spaces. The permanent identifiers are
-- 'contemporary' (Contemporary), 'spaces' (Spaces) and 'being' (Being), in these CHECK constraints, the Studio, the launch
-- switches and the public pages (plotart/gallery/, plotart/spaces/, plotart/being/).
--
-- Why a migration: migration 0023 (revision 4, applied in production on 25 Nov 2026) wrote 'environment' into the CHECK
-- constraints of its seven tables, and SQLite cannot change a CHECK constraint in place. The seven tables are recreated,
-- identical to 0023 revision 4 except that 'environment' is now 'spaces'.
--
-- Why this is safe now: the seven tables are EMPTY in production. Only the Phase B Studio code writes them, and that code has
-- never been deployed (the live Studio is 51d9adc, which does not know these tables). The first statement below PROVES it at
-- run time: if any of the seven tables holds even one row, it fails (json() refuses the malformed text) and the migration
-- stops BEFORE anything is dropped. Nothing else is touched: no existing table, row, column, index or trigger outside these
-- seven, no data inserted. Every artist, artwork, gallery position (01-25), Featured Artists selection, agreement,
-- commission term, payment record and image record stays exactly as it is.
--
-- Class: DESTRUCTIVE in the migration check's terms (it drops and recreates tables that already exist), so it runs in the
-- environment "studio-database" and waits for the founder's own Approve in GitHub, after the Time Travel restore point and
-- the encrypted export, and the fingerprint check that only the seven declared tables changed.
--
-- Preconditions before anyone runs it:
--   (1) migration 0023 revision 4 has run (it has: run 45578283948, 25 Nov 2026);
--   (2) the Phase B Studio (404986e) has NOT been deployed (or, if it has, the guard below decides);
--   (3) the founder has approved this exact file (SHA-256);
--   (4) it runs through studio-d1-migration; the new Studio (with 'spaces') is deployed only after it.
-- Re-running it is harmless while the tables are empty. Rollback: the Time Travel restore point (the tables were empty).
--
-- Revision 2 (25 Nov 2026, founder review of the safeguards): a closing check (step 4) verifies the result inside the same
-- run. wrangler d1 execute --remote --file sends the whole file through D1's import API, which wrangler documents as
-- returning the database to its original state if execution fails; the closing check makes any failure explicit and
-- would also catch an incomplete result, which the workflow's fingerprint comparison alone would not (a missing declared
-- table counts as a "declared table changed"). Nothing else differs from revision 1 (SHA 5dc8dfbb…, superseded).

-- 1 · the guard: refuses unless all seven tables are empty (nothing has been dropped yet if it refuses)
SELECT CASE WHEN ((SELECT COUNT(*) FROM gallery_settings) + (SELECT COUNT(*) FROM gallery_memberships) + (SELECT COUNT(*) FROM artwork_placements) + (SELECT COUNT(*) FROM gallery_order) + (SELECT COUNT(*) FROM gallery_features) + (SELECT COUNT(*) FROM image_use_requests) + (SELECT COUNT(*) FROM image_use_consents)) = 0 THEN 'the seven gallery tables are empty' ELSE json('REFUSED: a gallery table holds records; migration 0024 must not run') END AS guard;

-- 2 · drop the seven empty tables, children first (their indexes go with them)
DROP TABLE IF EXISTS image_use_consents;
DROP TABLE IF EXISTS image_use_requests;
DROP TABLE IF EXISTS gallery_features;
DROP TABLE IF EXISTS gallery_order;
DROP TABLE IF EXISTS artwork_placements;
DROP TABLE IF EXISTS gallery_memberships;
DROP TABLE IF EXISTS gallery_settings;

-- 3 · recreate them exactly as 0023 revision 4, with 'spaces' in place of 'environment'
-- @@DDL-BEGIN (schema.sql carries this block for new installs and local tests)
CREATE TABLE gallery_settings (
  gallery_id TEXT PRIMARY KEY CHECK (gallery_id IN ('contemporary', 'spaces', 'being')),
  status TEXT NOT NULL CHECK (status IN ('in_preparation', 'open', 'paused')),
  target_artists INTEGER NOT NULL CHECK (target_artists BETWEEN 0 AND 500),
  target_works INTEGER NOT NULL CHECK (target_works BETWEEN 0 AND 5000),
  opened_at TEXT,
  opened_by TEXT,
  updated_at TEXT NOT NULL CHECK (length(updated_at) BETWEEN 20 AND 30),
  updated_by TEXT NOT NULL,
  CHECK (gallery_id <> 'contemporary' OR status = 'open'),
  CHECK (status <> 'open' OR (opened_at IS NOT NULL AND opened_by IS NOT NULL))
);

CREATE TABLE gallery_memberships (
  artist_id TEXT NOT NULL REFERENCES artists(id) ON DELETE CASCADE,
  gallery_id TEXT NOT NULL CHECK (gallery_id IN ('contemporary', 'spaces', 'being')),
  state TEXT NOT NULL CHECK (state IN ('proposed', 'founder_approved', 'artist_accepted', 'live', 'declined', 'refused', 'withdrawn')),
  source TEXT NOT NULL CHECK (source IN ('existing_contemporary', 'founder_invitation', 'application', 'founder_curation', 'artist_request')),
  application_ref TEXT CHECK (application_ref IS NULL OR length(application_ref) BETWEEN 8 AND 40),
  proposed_by TEXT NOT NULL,
  proposed_at TEXT NOT NULL,
  founder_approved_by TEXT,
  founder_approved_at TEXT,
  artist_accepted_at TEXT,
  closed_by TEXT,
  closed_at TEXT,
  updated_at TEXT NOT NULL CHECK (length(updated_at) BETWEEN 20 AND 30),
  PRIMARY KEY (artist_id, gallery_id),
  CHECK (source <> 'application' OR application_ref IS NOT NULL),
  CHECK (state NOT IN ('founder_approved', 'live') OR (founder_approved_at IS NOT NULL AND founder_approved_by IS NOT NULL)),
  CHECK (state NOT IN ('artist_accepted', 'live') OR artist_accepted_at IS NOT NULL),
  CHECK (state NOT IN ('declined', 'refused', 'withdrawn') OR (closed_at IS NOT NULL AND closed_by IS NOT NULL))
);
CREATE INDEX gallery_memberships_gallery ON gallery_memberships(gallery_id, state);

CREATE TABLE artwork_placements (
  artwork_id TEXT NOT NULL REFERENCES artworks(id) ON DELETE CASCADE,
  artist_id TEXT NOT NULL REFERENCES artists(id) ON DELETE CASCADE,
  gallery_id TEXT NOT NULL CHECK (gallery_id IN ('contemporary', 'spaces', 'being')),
  state TEXT NOT NULL CHECK (state IN ('proposed', 'founder_approved', 'artist_accepted', 'live', 'declined', 'refused', 'withdrawn')),
  proposed_by TEXT NOT NULL,
  proposed_at TEXT NOT NULL,
  founder_approved_by TEXT,
  founder_approved_at TEXT,
  artist_accepted_at TEXT,
  closed_by TEXT,
  closed_at TEXT,
  updated_at TEXT NOT NULL CHECK (length(updated_at) BETWEEN 20 AND 30),
  PRIMARY KEY (artwork_id, gallery_id),
  CHECK (gallery_id <> 'contemporary' OR state = 'withdrawn'),
  CHECK (state NOT IN ('founder_approved', 'live') OR (founder_approved_at IS NOT NULL AND founder_approved_by IS NOT NULL)),
  CHECK (state NOT IN ('artist_accepted', 'live') OR artist_accepted_at IS NOT NULL),
  CHECK (state NOT IN ('declined', 'refused', 'withdrawn') OR (closed_at IS NOT NULL AND closed_by IS NOT NULL))
);
CREATE INDEX artwork_placements_gallery ON artwork_placements(gallery_id, state);
CREATE INDEX artwork_placements_artist ON artwork_placements(artist_id);

CREATE TABLE gallery_order (
  gallery_id TEXT NOT NULL CHECK (gallery_id IN ('contemporary', 'spaces', 'being')),
  position INTEGER NOT NULL CHECK (position >= 1 AND position <= 100000),
  artist_id TEXT NOT NULL REFERENCES artists(id) ON DELETE CASCADE,
  updated_at TEXT NOT NULL CHECK (length(updated_at) BETWEEN 20 AND 30),
  updated_by TEXT NOT NULL,
  PRIMARY KEY (gallery_id, position),
  UNIQUE (gallery_id, artist_id),
  CHECK (gallery_id <> 'contemporary' OR position >= 26)
);

CREATE TABLE gallery_features (
  gallery_id TEXT NOT NULL CHECK (gallery_id IN ('spaces', 'being')),
  position INTEGER NOT NULL CHECK (position BETWEEN 1 AND 6),
  artist_id TEXT NOT NULL REFERENCES artists(id) ON DELETE CASCADE,
  artwork_id TEXT NOT NULL REFERENCES artworks(id) ON DELETE CASCADE,
  updated_at TEXT NOT NULL CHECK (length(updated_at) BETWEEN 20 AND 30),
  updated_by TEXT NOT NULL,
  PRIMARY KEY (gallery_id, position),
  UNIQUE (gallery_id, artist_id)
);

CREATE TABLE image_use_requests (
  id TEXT PRIMARY KEY,
  artist_id TEXT NOT NULL REFERENCES artists(id) ON DELETE CASCADE,
  scope TEXT NOT NULL CHECK (scope IN ('homepage_feature', 'promotional_campaign', 'social_media', 'editorial_feature', 'video_feature')),
  gallery_id TEXT CHECK (gallery_id IS NULL OR gallery_id IN ('contemporary', 'spaces', 'being')),
  artwork_ids TEXT NOT NULL CHECK (length(artwork_ids) BETWEEN 2 AND 2000),
  purpose TEXT NOT NULL CHECK (length(purpose) BETWEEN 10 AND 600),
  channels TEXT NOT NULL CHECK (length(channels) BETWEEN 2 AND 300),
  valid_until TEXT,
  request_text_sha256 TEXT NOT NULL CHECK (length(request_text_sha256) = 64),
  status TEXT NOT NULL CHECK (status IN ('open', 'answered', 'cancelled')),
  requested_by TEXT NOT NULL,
  requested_at TEXT NOT NULL CHECK (length(requested_at) BETWEEN 20 AND 30),
  closed_at TEXT,
  CHECK (status = 'open' OR closed_at IS NOT NULL)
);
CREATE INDEX image_use_requests_artist ON image_use_requests(artist_id, status);

CREATE TABLE image_use_consents (
  id TEXT PRIMARY KEY,
  request_id TEXT REFERENCES image_use_requests(id) ON DELETE CASCADE,
  artist_id TEXT NOT NULL REFERENCES artists(id) ON DELETE CASCADE,
  scope TEXT NOT NULL CHECK (scope IN ('homepage_feature', 'promotional_campaign', 'social_media', 'editorial_feature', 'video_feature')),
  gallery_id TEXT CHECK (gallery_id IS NULL OR gallery_id IN ('contemporary', 'spaces', 'being')),
  artwork_ids TEXT NOT NULL CHECK (length(artwork_ids) BETWEEN 2 AND 2000),
  purpose TEXT NOT NULL CHECK (length(purpose) BETWEEN 10 AND 600),
  channels TEXT NOT NULL CHECK (length(channels) BETWEEN 2 AND 300),
  valid_until TEXT,
  answer TEXT NOT NULL CHECK (answer IN ('yes', 'no')),
  method TEXT NOT NULL CHECK (method IN ('studio', 'email_logged_by_founder')),
  request_text_sha256 TEXT NOT NULL CHECK (length(request_text_sha256) = 64),
  recorded_by TEXT NOT NULL,
  created_at TEXT NOT NULL CHECK (length(created_at) BETWEEN 20 AND 30)
);
CREATE INDEX image_use_consents_artist ON image_use_consents(artist_id, scope, created_at);
-- @@DDL-END

-- 4 · the closing check (revision 2): all seven tables and their five indexes exist, every table carries 'spaces' and none
-- 'environment'. If not, it fails, so the run fails visibly instead of passing with a partly recreated schema.
SELECT CASE WHEN (SELECT COUNT(*) FROM sqlite_master WHERE type = 'table' AND name IN ('gallery_settings', 'gallery_memberships', 'artwork_placements', 'gallery_order', 'gallery_features', 'image_use_requests', 'image_use_consents')
                    AND sql LIKE '%''spaces''%' AND sql NOT LIKE '%''environment''%') = 7
             AND (SELECT COUNT(*) FROM sqlite_master WHERE type = 'index' AND name IN ('gallery_memberships_gallery', 'artwork_placements_gallery', 'artwork_placements_artist', 'image_use_requests_artist', 'image_use_consents_artist')) = 5
       THEN 'the seven gallery tables and five indexes are in place with spaces'
       ELSE json('REFUSED: the gallery tables are not all in place; restore from the Time Travel bookmark') END AS closing_check;
