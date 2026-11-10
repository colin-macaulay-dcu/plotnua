-- PlotArt Studio · migration 0006 · Art for Hire (Stage 3B-1, development 10 Nov 2026)
-- PROPOSAL FOR FOUNDER APPROVAL. NOT RUN against any real database.
-- Additive only: six NEW tables, their indexes and refusal-only guards. No existing table, column, row, trigger,
-- agreement, gallery, enquiry route or document is changed. artists, artworks and enquiries are referenced, never written.
-- It installs NO document row: PA-AFH-2026-11 is not issued until it has had legal review (founder decision D10). Until a
-- hire_terms row exists, no acceptance can be recorded, so no artwork can be offered for hire.
-- Preconditions before anyone runs it:
--   (1) a fresh D1 backup (studio-d1-backup or the migration workflow's own two backups);
--   (2) the founder has approved this exact file (SHA-256) and its refusal-only guards;
--   (3) it runs through studio-d1-migration (environment studio-database, founder approval). Claude never runs it.
-- Foreign keys: artwork_hire and hire_enquiries CASCADE with their artwork / enquiry, so the Studio's existing deletions
-- (draft artwork delete, original erasure, the 24-month enquiry deletion) keep working unchanged. The four append-only
-- tables carry artist_id WITHOUT a foreign key to artists, so the existing six-year deletion of an artist row can never be
-- blocked by a hire record; the Stage 3B-2 code deletes those rows (once retention allows) before record_retention.
-- @@DDL-BEGIN (schema.sql carries this block verbatim for new installs and local tests)

-- 1 · The Art for Hire Artist Terms texts. A row is never changed or removed: a new text is a new identifier.
CREATE TABLE IF NOT EXISTS hire_terms (
  doc_id       TEXT PRIMARY KEY,                    -- e.g. 'PA-AFH-2026-11'
  title        TEXT NOT NULL,
  html_sha256  TEXT NOT NULL CHECK (length(html_sha256) = 64),
  pdf_sha256   TEXT NOT NULL CHECK (length(pdf_sha256) = 64),
  effective_at TEXT NOT NULL,                       -- no acceptance can be dated before this moment
  created_at   TEXT NOT NULL
);
CREATE TRIGGER IF NOT EXISTS hire_terms_no_update BEFORE UPDATE ON hire_terms
BEGIN SELECT RAISE(ABORT, 'hire_terms rows never change: install a new identifier'); END;
CREATE TRIGGER IF NOT EXISTS hire_terms_no_delete BEFORE DELETE ON hire_terms
BEGIN SELECT RAISE(ABORT, 'hire_terms rows are never removed'); END;

-- 2 · Each acceptance of the Art for Hire Artist Terms, separate from the Founding Artist Agreement and image licence
--     records (agreement_acceptances is not touched). One row per tick in Studio. Append-only.
CREATE TABLE IF NOT EXISTS hire_terms_acceptances (
  id            TEXT PRIMARY KEY,
  artist_id     TEXT NOT NULL,                      -- artists.id (no foreign key: see the header)
  doc_id        TEXT NOT NULL REFERENCES hire_terms(doc_id),
  doc_sha256    TEXT NOT NULL,
  pdf_sha256    TEXT NOT NULL,
  accepted_at   TEXT NOT NULL,
  account_email TEXT NOT NULL,
  display_name  TEXT NOT NULL,
  statement     TEXT NOT NULL,
  method        TEXT NOT NULL CHECK (method = 'studio_checkbox'),
  created_at    TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS hire_terms_acceptances_artist ON hire_terms_acceptances(artist_id, accepted_at);
CREATE TRIGGER IF NOT EXISTS hire_terms_acceptances_valid BEFORE INSERT ON hire_terms_acceptances
WHEN NOT EXISTS (SELECT 1 FROM hire_terms d WHERE d.doc_id = NEW.doc_id AND d.html_sha256 = NEW.doc_sha256
  AND d.pdf_sha256 = NEW.pdf_sha256 AND julianday(NEW.accepted_at) >= julianday(d.effective_at))
  OR NOT EXISTS (SELECT 1 FROM artists a WHERE a.id = NEW.artist_id)
BEGIN SELECT RAISE(ABORT, 'hire acceptance refused: unknown artist, not an installed text, wrong fingerprint, or dated before the text took effect'); END;
CREATE TRIGGER IF NOT EXISTS hire_terms_acceptances_no_update BEFORE UPDATE ON hire_terms_acceptances
BEGIN SELECT RAISE(ABORT, 'hire_terms_acceptances is append-only'); END;
CREATE TRIGGER IF NOT EXISTS hire_terms_acceptances_no_delete BEFORE DELETE ON hire_terms_acceptances
WHEN NOT EXISTS (SELECT 1 FROM record_retention r WHERE r.artist_id = OLD.artist_id AND julianday(r.delete_after) <= julianday('now'))
BEGIN SELECT RAISE(ABORT, 'hire_terms_acceptances is append-only until its retention period has ended'); END;

-- 3 · Leaving and rejoining Art for Hire (never edits an acceptance). Append-only.
CREATE TABLE IF NOT EXISTS hire_participation_events (
  id         TEXT PRIMARY KEY,
  artist_id  TEXT NOT NULL,                         -- artists.id (no foreign key: see the header)
  kind       TEXT NOT NULL CHECK (kind IN ('left', 'rejoined')),
  at         TEXT NOT NULL,
  actor      TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS hire_participation_events_artist ON hire_participation_events(artist_id, at);
CREATE TRIGGER IF NOT EXISTS hire_participation_events_no_update BEFORE UPDATE ON hire_participation_events
BEGIN SELECT RAISE(ABORT, 'hire_participation_events is append-only'); END;
CREATE TRIGGER IF NOT EXISTS hire_participation_events_no_delete BEFORE DELETE ON hire_participation_events
WHEN NOT EXISTS (SELECT 1 FROM record_retention r WHERE r.artist_id = OLD.artist_id AND julianday(r.delete_after) <= julianday('now'))
BEGIN SELECT RAISE(ABORT, 'hire_participation_events is append-only until its retention period has ended'); END;

-- 4 · The working hire details of one artwork. Editable by the Studio; deleted 30 days after withdrawal (Stage 3B-2 job).
--     NO price and NO replacement value columns (founder decisions 2 and 3). handling_note is private: never exported.
CREATE TABLE IF NOT EXISTS artwork_hire (
  artwork_id     TEXT PRIMARY KEY REFERENCES artworks(id) ON DELETE CASCADE,
  artist_id      TEXT NOT NULL REFERENCES artists(id) ON DELETE CASCADE,
  offered        INTEGER NOT NULL DEFAULT 0 CHECK (offered IN (0, 1)),          -- the opt-in switch: off by default
  availability   TEXT NOT NULL DEFAULT 'now' CHECK (availability IN ('now', 'from', 'not_now')),
  available_from TEXT,
  county         TEXT CHECK (county IS NULL OR length(county) <= 40),
  screen_use     TEXT NOT NULL DEFAULT 'none' CHECK (screen_use IN ('none', 'background', 'featured')),  -- willingness to discuss, never a licence
  photo_use      TEXT NOT NULL DEFAULT 'none' CHECK (photo_use IN ('none', 'yes')),                     -- willingness to discuss, never a licence
  framing        TEXT CHECK (framing IN ('framed', 'unframed', 'ready_to_hang')),
  glazed         INTEGER CHECK (glazed IN (0, 1)),
  weight_band    TEXT CHECK (weight_band IN ('under_5kg', '5_15kg', 'over_15kg')),
  handling_note  TEXT CHECK (handling_note IS NULL OR length(handling_note) <= 280),
  collection     TEXT NOT NULL DEFAULT 'ask' CHECK (collection IN ('collect', 'deliver_local', 'ask')),
  deliver_km     INTEGER CHECK (deliver_km IS NULL OR deliver_km BETWEEN 1 AND 500),
  review_state   TEXT NOT NULL DEFAULT 'draft' CHECK (review_state IN ('draft', 'pending', 'approved', 'declined')),
  approved_public TEXT,                             -- JSON of the PUBLIC fields as last approved by the founder
  approved_at    TEXT,
  approved_by    TEXT,
  decline_reason TEXT CHECK (decline_reason IS NULL OR length(decline_reason) <= 280),
  withdrawn_at   TEXT,
  updated_at     TEXT NOT NULL,
  created_at     TEXT NOT NULL,
  CHECK (availability <> 'from' OR available_from IS NOT NULL),
  CHECK (collection = 'deliver_local' OR deliver_km IS NULL),
  CHECK (review_state <> 'approved' OR (approved_public IS NOT NULL AND approved_at IS NOT NULL AND approved_by IS NOT NULL))
);
CREATE INDEX IF NOT EXISTS artwork_hire_artist ON artwork_hire(artist_id);
CREATE INDEX IF NOT EXISTS artwork_hire_listing ON artwork_hire(offered, review_state);

-- 5 · Separate, recorded permission for each specific lookbook or promotional use (Artist Terms 4.2). Append-only.
CREATE TABLE IF NOT EXISTS hire_use_permissions (
  id          TEXT PRIMARY KEY,
  artist_id   TEXT NOT NULL,                        -- artists.id (no foreign key: see the header)
  use_kind    TEXT NOT NULL CHECK (use_kind IN ('lookbook', 'social', 'press', 'other')),
  purpose     TEXT NOT NULL CHECK (length(purpose) BETWEEN 5 AND 500),
  recipients  TEXT NOT NULL CHECK (length(recipients) BETWEEN 2 AND 500),
  artwork_ids TEXT NOT NULL,                        -- JSON array of artworks.id
  answer      TEXT NOT NULL CHECK (answer IN ('yes', 'no')),
  answered_at TEXT NOT NULL,
  method      TEXT NOT NULL CHECK (method IN ('studio', 'email_logged_by_founder')),
  recorded_by TEXT NOT NULL,
  created_at  TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS hire_use_permissions_artist ON hire_use_permissions(artist_id, answered_at);
CREATE TRIGGER IF NOT EXISTS hire_use_permissions_no_update BEFORE UPDATE ON hire_use_permissions
BEGIN SELECT RAISE(ABORT, 'hire_use_permissions is append-only; record a new answer'); END;
CREATE TRIGGER IF NOT EXISTS hire_use_permissions_no_delete BEFORE DELETE ON hire_use_permissions
WHEN NOT EXISTS (SELECT 1 FROM record_retention r WHERE r.artist_id = OLD.artist_id AND julianday(r.delete_after) <= julianday('now'))
BEGIN SELECT RAISE(ABORT, 'hire_use_permissions is append-only until its retention period has ended'); END;

-- 6 · Hire-specific details of a commercial hire enquiry. The core enquiry stays in enquiries + enquiry_log (unchanged);
--     these details are deleted with the enquiry (CASCADE) or by their own 24-month delete_after.
CREATE TABLE IF NOT EXISTS hire_enquiries (
  enquiry_id     TEXT PRIMARY KEY REFERENCES enquiries(id) ON DELETE CASCADE,
  business       TEXT NOT NULL CHECK (length(business) BETWEEN 2 AND 160),
  role           TEXT NOT NULL CHECK (length(role) BETWEEN 2 AND 80),
  business_url   TEXT CHECK (business_url IS NULL OR length(business_url) <= 300),
  phone          TEXT CHECK (phone IS NULL OR length(phone) <= 40),
  project_type   TEXT NOT NULL CHECK (project_type IN ('film_tv', 'advertising', 'photography', 'staging', 'interiors', 'other')),
  date_from      TEXT,
  date_to        TEXT,
  intended_use   TEXT NOT NULL CHECK (intended_use IN ('display_staging', 'photography', 'filming', 'other')),
  use_county     TEXT CHECK (use_county IS NULL OR length(use_county) <= 40),
  territory_flag TEXT CHECK (territory_flag IN ('ie', 'ni', 'gb', 'other')),
  delete_after   TEXT NOT NULL,
  created_at     TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS hire_enquiries_delete_after ON hire_enquiries(delete_after);
-- @@DDL-END

-- Rollback (separately approved, after a backup; drops only what this migration created):
-- DROP TABLE IF EXISTS hire_enquiries;
-- DROP TABLE IF EXISTS hire_use_permissions;
-- DROP TABLE IF EXISTS artwork_hire;
-- DROP TABLE IF EXISTS hire_participation_events;
-- DROP TABLE IF EXISTS hire_terms_acceptances;
-- DROP TABLE IF EXISTS hire_terms;
