-- PlotArt Studio · migration 0012 · Gallery Artist terms and agreement records (development 13 Nov 2026)
-- PROPOSAL FOR FOUNDER APPROVAL. NOT RUN against any real database.
-- Creates THREE NEW tables and nothing else. No existing table, column, row, trigger, agreement, acceptance, gallery,
-- artwork or enquiry is read, changed or removed. Every existing artist, Founding or not, keeps exactly the documents and
-- behaviour they have today: an artist is on the Gallery Artist terms only if the founder invites them as one (a row here).
--   (1) artist_terms: the commercial terms of each Gallery Artist (track, commission rate in basis points, 15% unless a
--       written individual variation says otherwise, the date of that variation and a private founder note). Founding
--       Artists have no row. Never published; never exported to the website; shown to the artist only as their own terms.
--   (2) gallery_agreement_documents: the Gallery Artist Agreement texts an artist can accept (fixed text, fingerprints,
--       effective date). Empty after this migration: the approved PA-GAA text is installed by its own approved step (0013).
--   (3) gallery_agreement_acceptances: every acceptance of a Gallery Artist Agreement, append-only, exactly as
--       agreement_acceptances records Founding Artist acceptances. The image licence (PA-GPIL-2026-11) accepted in the same
--       tick is recorded in agreement_acceptances as today, under the same event_id.
-- Why new tables rather than widening agreement_documents: SQLite cannot widen a CHECK in place, and a rebuild of a table
-- that holds acceptance records would need PRAGMA writes and new triggers on an existing table, both of which the migration
-- safeguards refuse. New tables keep every existing record untouched and carry the same guards.
-- Numbering (13 Nov 2026): 0010 and 0011 have run in production; 0008 (Art for Hire hire reports) has not and is not
-- touched. This is 0012; the approved PA-GAA text is 0013; sale reports and commission records will be 0014.
-- Preconditions before anyone runs it: (1) the founder has approved this exact file (SHA-256) and its refusal-only guards;
-- (2) it runs through studio-d1-migration (two backups first; the guards mean it always waits for the founder's approval).
-- @@DDL-BEGIN (schema.sql carries this block verbatim for new installs and local tests)

CREATE TABLE IF NOT EXISTS artist_terms (
  artist_id           TEXT PRIMARY KEY REFERENCES artists(id),
  track               TEXT NOT NULL CHECK (track IN ('gallery_artist')),
  commission_bp       INTEGER NOT NULL DEFAULT 1500 CHECK (commission_bp BETWEEN 0 AND 1500),   -- 15% = 1500; never above
  variation_agreed_on TEXT CHECK (variation_agreed_on IS NULL OR variation_agreed_on GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'),
  variation_note      TEXT CHECK (variation_note IS NULL OR length(variation_note) <= 1000),        -- private to the founder
  set_by              TEXT NOT NULL,
  created_at          TEXT NOT NULL,
  updated_at          TEXT NOT NULL,
  -- anything other than the standard 15% needs a written individual variation (agreement clause 13)
  CHECK (commission_bp = 1500 OR variation_agreed_on IS NOT NULL)
);
CREATE TRIGGER IF NOT EXISTS artist_terms_track_fixed BEFORE UPDATE ON artist_terms
WHEN NEW.track <> OLD.track OR NEW.artist_id <> OLD.artist_id
BEGIN SELECT RAISE(ABORT, 'an artist''s track never changes here: a different programme needs a new, expressly accepted agreement'); END;
CREATE TRIGGER IF NOT EXISTS artist_terms_no_delete BEFORE DELETE ON artist_terms
WHEN NOT EXISTS (SELECT 1 FROM record_retention r WHERE r.artist_id = OLD.artist_id AND julianday(r.delete_after) <= julianday('now'))
BEGIN SELECT RAISE(ABORT, 'artist_terms is kept until its retention period has ended'); END;

CREATE TABLE IF NOT EXISTS gallery_agreement_documents (
  doc_id       TEXT PRIMARY KEY,
  kind         TEXT NOT NULL CHECK (kind IN ('gallery_artist_agreement')),
  title        TEXT NOT NULL,
  text_status  TEXT NOT NULL CHECK (text_status IN ('fixed')),
  html_sha256  TEXT NOT NULL CHECK (length(html_sha256) = 64),
  pdf_sha256   TEXT NOT NULL CHECK (length(pdf_sha256) = 64),
  effective_at TEXT NOT NULL,
  created_at   TEXT NOT NULL
);
CREATE TRIGGER IF NOT EXISTS gallery_agreement_documents_no_update BEFORE UPDATE ON gallery_agreement_documents
BEGIN SELECT RAISE(ABORT, 'gallery_agreement_documents rows never change: install a new identifier'); END;
CREATE TRIGGER IF NOT EXISTS gallery_agreement_documents_no_delete BEFORE DELETE ON gallery_agreement_documents
BEGIN SELECT RAISE(ABORT, 'gallery_agreement_documents rows are never removed'); END;

CREATE TABLE IF NOT EXISTS gallery_agreement_acceptances (
  id            TEXT PRIMARY KEY,
  event_id      TEXT NOT NULL,                      -- the same event_id as the PA-GPIL row in agreement_acceptances
  artist_id     TEXT NOT NULL REFERENCES artists(id),
  doc_id        TEXT NOT NULL REFERENCES gallery_agreement_documents(doc_id),
  doc_sha256    TEXT NOT NULL CHECK (length(doc_sha256) = 64),
  pdf_sha256    TEXT NOT NULL CHECK (length(pdf_sha256) = 64),
  accepted_at   TEXT NOT NULL,
  account_email TEXT NOT NULL,
  display_name  TEXT NOT NULL,
  legal_name    TEXT CHECK (legal_name IS NULL OR length(legal_name) BETWEEN 2 AND 120),
  method        TEXT NOT NULL CHECK (method IN ('studio_checkbox')),
  statement     TEXT NOT NULL,
  note          TEXT,
  created_at    TEXT NOT NULL,
  UNIQUE (event_id, doc_id)
);
CREATE INDEX IF NOT EXISTS gallery_agreement_acceptances_artist ON gallery_agreement_acceptances(artist_id, doc_id, accepted_at);
CREATE TRIGGER IF NOT EXISTS gallery_agreement_acceptances_valid BEFORE INSERT ON gallery_agreement_acceptances
WHEN NOT EXISTS (SELECT 1 FROM gallery_agreement_documents d WHERE d.doc_id = NEW.doc_id AND d.html_sha256 = NEW.doc_sha256
  AND d.pdf_sha256 = NEW.pdf_sha256 AND julianday(NEW.accepted_at) >= julianday(d.effective_at))
BEGIN SELECT RAISE(ABORT, 'acceptance refused: not an installed text, wrong fingerprint, or dated before the text took effect'); END;
CREATE TRIGGER IF NOT EXISTS gallery_agreement_acceptances_no_update BEFORE UPDATE ON gallery_agreement_acceptances
BEGIN SELECT RAISE(ABORT, 'gallery_agreement_acceptances is append-only'); END;
CREATE TRIGGER IF NOT EXISTS gallery_agreement_acceptances_no_delete BEFORE DELETE ON gallery_agreement_acceptances
WHEN NOT EXISTS (SELECT 1 FROM record_retention r WHERE r.artist_id = OLD.artist_id AND julianday(r.delete_after) <= julianday('now'))
BEGIN SELECT RAISE(ABORT, 'gallery_agreement_acceptances is append-only until its retention period has ended'); END;

-- @@DDL-END

-- Rollback (separately approved, after a backup; only while no Gallery Artist has been invited or has accepted):
-- DROP TABLE gallery_agreement_acceptances; DROP TABLE gallery_agreement_documents; DROP TABLE artist_terms;
