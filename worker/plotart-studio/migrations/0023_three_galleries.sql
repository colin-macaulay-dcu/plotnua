-- PlotArt Studio · migration 0023 · Three galleries: the gallery data model (Phase B, development 24 Nov 2026)
-- PROPOSAL FOR FOUNDER APPROVAL. NOT RUN against any real database.
-- ADDITIVE: creates SEVEN new tables and their indexes, and nothing else. No existing table, row, column or index is touched;
-- no data is inserted; no trigger. Every existing artist, artwork, gallery position (01-25), Featured Artists selection,
-- agreement, commission term, payment record and image record stays exactly as it is.
--
-- What the tables hold (the rules that use them live in src/galleries.js):
--   gallery_settings     the founder's readiness targets and the open / in preparation / paused status of each gallery.
--                        Empty until the founder changes something: the defaults are in code (Contemporary Art open;
--                        Landscape Art and Portraiture in preparation, target 6 artists and 30 works).
--   gallery_memberships  an artist's membership of a gallery: proposed, approved by the founder, accepted by the artist, live,
--                        and how it began (founder invitation, application, founder curation, artist request). An artist with
--                        no membership rows at all is a live Contemporary Art member, exactly as today: existing artists are
--                        never copied, moved or assigned anywhere by this migration.
--   artwork_placements   an artwork's placement in Landscape Art or Portraiture (founder approval and artist acceptance), and
--                        the only way a work can be taken out of Contemporary Art (an explicit 'withdrawn' row).
--   gallery_order        unlimited curated order per gallery. Contemporary Art keeps positions 01-25 in gallery_positions
--                        (unchanged, still guarded); this table holds Contemporary positions from 26 and every position of
--                        the other two galleries.
--   gallery_features     Artists in Focus for Landscape Art and Portraiture (up to six each). Contemporary Art keeps
--                        homepage_features (migration 0016), unchanged.
--   image_use_requests   the founder's request to use specific artworks for one purpose (homepage, campaign, social media,
--                        editorial, video), per use, as licence PA-GPIL §3.2 requires. No standing opt-in.
--   image_use_consents   the artist's recorded answer (yes or no), append-only: the Studio never updates or deletes a row;
--                        a withdrawal is a new 'no'.
--
-- Revision 2 (24 Nov 2026, final verification): every reference from these new tables to artists, artworks or a request is
-- ON DELETE CASCADE. D1 enforces foreign keys, so without it the Studio's existing deletions (an artist deleting a draft
-- artwork; erasing an ended artist's originals after 12 months; deleting their records after six years) would be refused
-- once a gallery row pointed at the artwork or artist. With it, those deletions work exactly as today and take the matching
-- gallery rows with them. Nothing cascades the other way: no existing row is ever deleted or changed by these tables.
--
-- Preconditions before anyone runs it:
--   (1) migrations up to 0022 have run;
--   (2) the founder has approved this exact file (SHA-256);
--   (3) it runs through studio-d1-migration (Time Travel restore point and encrypted export first, then the check that only
--       the declared tables changed). Claude never runs it outside that workflow.
-- Re-running it is harmless (IF NOT EXISTS).
-- @@DDL-BEGIN (schema.sql carries this block verbatim for new installs and local tests)

CREATE TABLE IF NOT EXISTS gallery_settings (
  gallery_id TEXT PRIMARY KEY CHECK (gallery_id IN ('contemporary', 'landscape', 'portraiture')),
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

CREATE TABLE IF NOT EXISTS gallery_memberships (
  artist_id TEXT NOT NULL REFERENCES artists(id) ON DELETE CASCADE,
  gallery_id TEXT NOT NULL CHECK (gallery_id IN ('contemporary', 'landscape', 'portraiture')),
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
CREATE INDEX IF NOT EXISTS gallery_memberships_gallery ON gallery_memberships(gallery_id, state);

CREATE TABLE IF NOT EXISTS artwork_placements (
  artwork_id TEXT NOT NULL REFERENCES artworks(id) ON DELETE CASCADE,
  artist_id TEXT NOT NULL REFERENCES artists(id) ON DELETE CASCADE,
  gallery_id TEXT NOT NULL CHECK (gallery_id IN ('contemporary', 'landscape', 'portraiture')),
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
CREATE INDEX IF NOT EXISTS artwork_placements_gallery ON artwork_placements(gallery_id, state);
CREATE INDEX IF NOT EXISTS artwork_placements_artist ON artwork_placements(artist_id);

CREATE TABLE IF NOT EXISTS gallery_order (
  gallery_id TEXT NOT NULL CHECK (gallery_id IN ('contemporary', 'landscape', 'portraiture')),
  position INTEGER NOT NULL CHECK (position >= 1 AND position <= 100000),
  artist_id TEXT NOT NULL REFERENCES artists(id) ON DELETE CASCADE,
  updated_at TEXT NOT NULL CHECK (length(updated_at) BETWEEN 20 AND 30),
  updated_by TEXT NOT NULL,
  PRIMARY KEY (gallery_id, position),
  UNIQUE (gallery_id, artist_id),
  CHECK (gallery_id <> 'contemporary' OR position >= 26)
);

CREATE TABLE IF NOT EXISTS gallery_features (
  gallery_id TEXT NOT NULL CHECK (gallery_id IN ('landscape', 'portraiture')),
  position INTEGER NOT NULL CHECK (position BETWEEN 1 AND 6),
  artist_id TEXT NOT NULL REFERENCES artists(id) ON DELETE CASCADE,
  artwork_id TEXT NOT NULL REFERENCES artworks(id) ON DELETE CASCADE,
  updated_at TEXT NOT NULL CHECK (length(updated_at) BETWEEN 20 AND 30),
  updated_by TEXT NOT NULL,
  PRIMARY KEY (gallery_id, position),
  UNIQUE (gallery_id, artist_id)
);

CREATE TABLE IF NOT EXISTS image_use_requests (
  id TEXT PRIMARY KEY,
  artist_id TEXT NOT NULL REFERENCES artists(id) ON DELETE CASCADE,
  scope TEXT NOT NULL CHECK (scope IN ('homepage_feature', 'promotional_campaign', 'social_media', 'editorial_feature', 'video_feature')),
  gallery_id TEXT CHECK (gallery_id IS NULL OR gallery_id IN ('contemporary', 'landscape', 'portraiture')),
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
CREATE INDEX IF NOT EXISTS image_use_requests_artist ON image_use_requests(artist_id, status);

CREATE TABLE IF NOT EXISTS image_use_consents (
  id TEXT PRIMARY KEY,
  request_id TEXT REFERENCES image_use_requests(id) ON DELETE CASCADE,
  artist_id TEXT NOT NULL REFERENCES artists(id) ON DELETE CASCADE,
  scope TEXT NOT NULL CHECK (scope IN ('homepage_feature', 'promotional_campaign', 'social_media', 'editorial_feature', 'video_feature')),
  gallery_id TEXT CHECK (gallery_id IS NULL OR gallery_id IN ('contemporary', 'landscape', 'portraiture')),
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
CREATE INDEX IF NOT EXISTS image_use_consents_artist ON image_use_consents(artist_id, scope, created_at);

-- @@DDL-END

-- Rollback (separately approved; removes only the gallery model, nothing that existed before it):
-- DROP TABLE image_use_consents;
-- DROP TABLE image_use_requests;
-- DROP TABLE gallery_features;
-- DROP TABLE gallery_order;
-- DROP TABLE artwork_placements;
-- DROP TABLE gallery_memberships;
-- DROP TABLE gallery_settings;
