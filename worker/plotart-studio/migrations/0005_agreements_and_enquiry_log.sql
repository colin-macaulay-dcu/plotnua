-- PlotArt Studio · migration 0005 · Founding Artist Agreement acceptance records and the enquiry log
-- FINAL PROPOSAL (development, 6 Nov 2026) FOR FOUNDER APPROVAL. NOT RUN against any real database.
-- Additive only: no existing table, column or row is changed or deleted. artists and enquiries are read, never written.
-- Preconditions before anyone runs it (release sequence step 4):
--   (1) the founder has approved PA-FAA-2026-11 and PA-GPIL-2026-11 for issue; the fingerprints below are those of the
--       exact files in worker/plotart-studio/agreements/issued/ (checked by test/prove-migration-0005.mjs);
--   (2) the website release that adds PA-GPIL-2026-11 to the publishing safeguards is live;
--   (3) a D1 backup has been taken (studio-d1-backup workflow) and the read-only "before" counts in section 7 noted;
--   (4) the founder runs it himself (D1 console or the studio-d1-migration workflow). Claude never runs it.
-- It runs once: a second run stops at the first INSERT (the document rows already exist) and changes nothing.
-- @@DDL-BEGIN (schema.sql carries this block verbatim for new installs and local tests)

-- 1 · The documents an artist can accept. A row is never changed or removed once installed: a new text is a new row.
CREATE TABLE IF NOT EXISTS agreement_documents (
  doc_id       TEXT PRIMARY KEY,
  kind         TEXT NOT NULL CHECK (kind IN ('founding_artist_agreement', 'gallery_licence')),
  title        TEXT NOT NULL,
  text_status  TEXT NOT NULL CHECK (text_status IN ('fixed', 'label_only')),
  html_sha256  TEXT,                                -- fingerprint of the exact page Studio shows
  pdf_sha256   TEXT,                                -- fingerprint of the exact PDF Studio serves
  effective_at TEXT NOT NULL,                       -- no acceptance can be recorded before this moment
  created_at   TEXT NOT NULL,
  CHECK ((text_status = 'fixed' AND length(html_sha256) = 64 AND length(pdf_sha256) = 64)
      OR (text_status = 'label_only' AND html_sha256 IS NULL AND pdf_sha256 IS NULL))
);
CREATE TRIGGER IF NOT EXISTS agreement_documents_no_update BEFORE UPDATE ON agreement_documents
BEGIN SELECT RAISE(ABORT, 'agreement_documents rows never change: install a new identifier'); END;
CREATE TRIGGER IF NOT EXISTS agreement_documents_no_delete BEFORE DELETE ON agreement_documents
BEGIN SELECT RAISE(ABORT, 'agreement_documents rows are never removed'); END;

-- 2 · Retention (agreement 11.2: the agreement's life plus six years). One row per artist whose participation has ended,
--     written once by the founder's "End participation" step. Rows in the append-only tables below can be deleted ONLY
--     when their artist's delete_after has passed; nothing else can delete them.
CREATE TABLE IF NOT EXISTS record_retention (
  artist_id    TEXT PRIMARY KEY REFERENCES artists(id),
  ended_at     TEXT NOT NULL,
  delete_after TEXT NOT NULL,
  recorded_by  TEXT NOT NULL,
  recorded_at  TEXT NOT NULL,
  CHECK (julianday(delete_after) >= julianday(ended_at, '+6 years'))
);
CREATE TRIGGER IF NOT EXISTS record_retention_no_update BEFORE UPDATE ON record_retention
BEGIN SELECT RAISE(ABORT, 'record_retention rows never change'); END;
CREATE TRIGGER IF NOT EXISTS record_retention_no_delete BEFORE DELETE ON record_retention
WHEN EXISTS (SELECT 1 FROM agreement_acceptances WHERE artist_id = OLD.artist_id) OR EXISTS (SELECT 1 FROM enquiry_log WHERE artist_id = OLD.artist_id)
  OR EXISTS (SELECT 1 FROM acceptance_corrections WHERE artist_id = OLD.artist_id) OR EXISTS (SELECT 1 FROM participation_events WHERE artist_id = OLD.artist_id)
BEGIN SELECT RAISE(ABORT, 'delete the records this retention row covers first'); END;

-- 3 · Every acceptance, append-only. One tick in Studio = one event_id = one row per document accepted.
CREATE TABLE IF NOT EXISTS agreement_acceptances (
  id            TEXT PRIMARY KEY,
  event_id      TEXT NOT NULL,
  artist_id     TEXT NOT NULL REFERENCES artists(id),
  doc_id        TEXT NOT NULL REFERENCES agreement_documents(doc_id),
  doc_sha256    TEXT,                               -- the html fingerprint of the text shown at that moment
  pdf_sha256    TEXT,                               -- the PDF fingerprint offered for download at that moment
  accepted_at   TEXT NOT NULL,                      -- ISO 8601 UTC (shown in Irish time)
  account_email TEXT,                               -- the signed-in Studio address at that moment
  display_name  TEXT,                               -- professional name at that moment
  legal_name    TEXT,                               -- optional: entered by the artist if they wish
  method        TEXT NOT NULL CHECK (method IN ('studio_checkbox', 'migrated_from_artists_table')),
  statement     TEXT NOT NULL,                      -- the exact words beside the box the artist ticked
  note          TEXT,
  created_at    TEXT NOT NULL,
  CHECK (method = 'migrated_from_artists_table' OR (account_email IS NOT NULL AND display_name IS NOT NULL AND length(doc_sha256) = 64 AND length(pdf_sha256) = 64)),
  -- a migrated row can only ever carry the legacy label: no agreement acceptance can be created retrospectively
  CHECK (method = 'studio_checkbox' OR (doc_id = 'PA-GPIL-2026-10-29' AND doc_sha256 IS NULL AND account_email IS NULL AND legal_name IS NULL)),
  CHECK (legal_name IS NULL OR length(legal_name) BETWEEN 2 AND 120),
  UNIQUE (event_id, doc_id)
);
CREATE INDEX IF NOT EXISTS agreement_acceptances_artist ON agreement_acceptances(artist_id, doc_id, accepted_at);
-- A Studio acceptance must name an installed fixed text, carry exactly its fingerprints, and not predate it.
CREATE TRIGGER IF NOT EXISTS agreement_acceptances_valid BEFORE INSERT ON agreement_acceptances
WHEN NEW.method = 'studio_checkbox' AND NOT EXISTS (SELECT 1 FROM agreement_documents d WHERE d.doc_id = NEW.doc_id AND d.text_status = 'fixed'
  AND d.html_sha256 = NEW.doc_sha256 AND d.pdf_sha256 = NEW.pdf_sha256 AND julianday(NEW.accepted_at) >= julianday(d.effective_at))
BEGIN SELECT RAISE(ABORT, 'acceptance refused: not an installed text, wrong fingerprint, or dated before the text took effect'); END;
CREATE TRIGGER IF NOT EXISTS agreement_acceptances_no_update BEFORE UPDATE ON agreement_acceptances
BEGIN SELECT RAISE(ABORT, 'agreement_acceptances is append-only'); END;
CREATE TRIGGER IF NOT EXISTS agreement_acceptances_no_delete BEFORE DELETE ON agreement_acceptances
WHEN NOT EXISTS (SELECT 1 FROM record_retention r WHERE r.artist_id = OLD.artist_id AND julianday(r.delete_after) <= julianday('now'))
BEGIN SELECT RAISE(ABORT, 'agreement_acceptances is append-only until its retention period has ended'); END;

-- 4 · The enquiry log: one row per enquiry PlotArt introduces, by any route, with NO buyer contact details. Relay enquiries
--     get a row automatically; enquiries introduced by email get a row when the founder uses "Log enquiry". The relay table
--     (enquiries: the buyer's name, email and message) is untouched and is still deleted at 24 months by the daily clean-up.
--     Still personal data (it identifies the artist; a buyer could be re-identified through the reference sent to them):
--     kept for the agreement's life plus six years (agreement 5.5), then deletable under section 2.
CREATE TABLE IF NOT EXISTS enquiry_log (
  id                TEXT PRIMARY KEY,
  reference         TEXT NOT NULL UNIQUE,           -- relay: the enquiry's own PA-E-... reference; email: PA-EM-...
  artist_id         TEXT NOT NULL REFERENCES artists(id),
  artwork_id        TEXT,
  route             TEXT NOT NULL CHECK (route IN ('relay', 'email')),
  introduced_at     TEXT NOT NULL,                  -- when PlotArt introduced the enquiry (ISO 8601 UTC)
  founding          INTEGER NOT NULL CHECK (founding IN (0, 1)),
  founding_year_end TEXT,                           -- the founding year's last day (Irish date) used for that decision
  logged_by         TEXT NOT NULL,                  -- 'relay', 'migration 0005' or the founder's Studio address
  logged_at         TEXT NOT NULL,
  late_entry        INTEGER NOT NULL DEFAULT 0 CHECK (late_entry IN (0, 1)),
  corrects          TEXT REFERENCES enquiry_log(id),
  note              TEXT CHECK (note IS NULL OR length(note) <= 280),
  CHECK (route = 'relay' OR reference GLOB 'PA-EM-*'),
  CHECK (julianday(introduced_at) <= julianday(logged_at))
);
CREATE INDEX IF NOT EXISTS enquiry_log_artist ON enquiry_log(artist_id, introduced_at);
CREATE TRIGGER IF NOT EXISTS enquiry_log_no_update BEFORE UPDATE ON enquiry_log
BEGIN SELECT RAISE(ABORT, 'enquiry_log is append-only; add a correcting row'); END;
CREATE TRIGGER IF NOT EXISTS enquiry_log_no_delete BEFORE DELETE ON enquiry_log
WHEN NOT EXISTS (SELECT 1 FROM record_retention r WHERE r.artist_id = OLD.artist_id AND julianday(r.delete_after) <= julianday('now'))
BEGIN SELECT RAISE(ABORT, 'enquiry_log is append-only until its retention period has ended'); END;

-- 4b · Corrections to acceptance records (founder decision 6 Nov 2026). A mistyped legal name or another factual error in
--      a recorded acceptance is corrected by a SEPARATE row linked to it, with a reason and a time. The acceptance row is
--      never changed: its documents, version, fingerprints, acceptance time and statement cannot be corrected at all (no
--      column exists for them here), and a correction is not an acceptance.
CREATE TABLE IF NOT EXISTS acceptance_corrections (
  id              TEXT PRIMARY KEY,
  acceptance_id   TEXT NOT NULL REFERENCES agreement_acceptances(id),
  artist_id       TEXT NOT NULL REFERENCES artists(id),
  correction_group TEXT NOT NULL,                  -- one founder action across the rows of one acceptance event
  field           TEXT NOT NULL CHECK (field IN ('legal_name', 'display_name', 'account_email')),
  previous_value  TEXT,                            -- the value shown before this correction (original or earlier correction)
  corrected_value TEXT,                            -- NULL only to remove a legal name entered in error
  reason          TEXT NOT NULL CHECK (length(reason) BETWEEN 10 AND 280),
  requested_by    TEXT NOT NULL CHECK (requested_by IN ('artist', 'founder')),
  corrected_by    TEXT NOT NULL,
  corrected_at    TEXT NOT NULL,
  CHECK (corrected_value IS NOT NULL OR field = 'legal_name'),
  UNIQUE (correction_group, acceptance_id)
);
CREATE INDEX IF NOT EXISTS acceptance_corrections_acc ON acceptance_corrections(acceptance_id, corrected_at);
-- the artist must be the one the acceptance belongs to; a label-only (migrated) record never gains a legal name or address
CREATE TRIGGER IF NOT EXISTS acceptance_corrections_valid BEFORE INSERT ON acceptance_corrections
WHEN NOT EXISTS (SELECT 1 FROM agreement_acceptances a WHERE a.id = NEW.acceptance_id AND a.artist_id = NEW.artist_id
  AND julianday(NEW.corrected_at) >= julianday(a.accepted_at) AND (a.method = 'studio_checkbox' OR NEW.field = 'display_name'))
BEGIN SELECT RAISE(ABORT, 'correction refused: not this artist''s acceptance, dated before it, or a field a label-only record never held'); END;
CREATE TRIGGER IF NOT EXISTS acceptance_corrections_no_update BEFORE UPDATE ON acceptance_corrections
BEGIN SELECT RAISE(ABORT, 'acceptance_corrections is append-only; add a further correction'); END;
CREATE TRIGGER IF NOT EXISTS acceptance_corrections_no_delete BEFORE DELETE ON acceptance_corrections
WHEN NOT EXISTS (SELECT 1 FROM record_retention r WHERE r.artist_id = OLD.artist_id AND julianday(r.delete_after) <= julianday('now'))
BEGIN SELECT RAISE(ABORT, 'acceptance_corrections is append-only until its retention period has ended'); END;

-- 4c · Ending participation (founder decision 6 Nov 2026): the artist's request to leave, the founder's ending, the gallery
--      removal and each scheduled deletion, as an append-only log. The current state is read from it; nothing is overwritten.
CREATE TABLE IF NOT EXISTS participation_events (
  id         TEXT PRIMARY KEY,
  artist_id  TEXT NOT NULL REFERENCES artists(id),
  kind       TEXT NOT NULL CHECK (kind IN ('leave_requested', 'leave_request_withdrawn', 'ended', 'originals_deleted')),
  at         TEXT NOT NULL,
  actor      TEXT NOT NULL,
  reason     TEXT CHECK (reason IS NULL OR length(reason) <= 280),
  detail     TEXT
);
CREATE INDEX IF NOT EXISTS participation_events_artist ON participation_events(artist_id, at);
CREATE TRIGGER IF NOT EXISTS participation_events_one_ending BEFORE INSERT ON participation_events
WHEN NEW.kind = 'ended' AND EXISTS (SELECT 1 FROM participation_events WHERE artist_id = NEW.artist_id AND kind = 'ended')
BEGIN SELECT RAISE(ABORT, 'participation has already ended'); END;
CREATE TRIGGER IF NOT EXISTS participation_events_no_update BEFORE UPDATE ON participation_events
BEGIN SELECT RAISE(ABORT, 'participation_events is append-only'); END;
CREATE TRIGGER IF NOT EXISTS participation_events_no_delete BEFORE DELETE ON participation_events
WHEN NOT EXISTS (SELECT 1 FROM record_retention r WHERE r.artist_id = OLD.artist_id AND julianday(r.delete_after) <= julianday('now'))
BEGIN SELECT RAISE(ABORT, 'participation_events is append-only until its retention period has ended'); END;
-- @@DDL-END

-- 5 · The documents. The fingerprints are those of agreements/issued/ (fingerprints.json); effective from the moment this runs.
INSERT INTO agreement_documents (doc_id, kind, title, text_status, html_sha256, pdf_sha256, effective_at, created_at) VALUES
 ('PA-GPIL-2026-10-29', 'gallery_licence', 'PlotArt Gallery Publication and Image Licence', 'label_only', NULL, NULL,
  '2026-10-29T00:00:00Z', strftime('%Y-%m-%dT%H:%M:%SZ','now')),
 ('PA-GPIL-2026-11', 'gallery_licence', 'PlotArt Gallery Publication and Image Licence', 'fixed',
  'f4a2c72e8068a267afac87a7555ac509fb64d9b9a9385f389a855d5ba8408f92', 'aa3c27423f21877006bac7bd5e3132111dea5e2914617cf30826b4203637ba17',
  strftime('%Y-%m-%dT%H:%M:%SZ','now'), strftime('%Y-%m-%dT%H:%M:%SZ','now')),
 ('PA-FAA-2026-11', 'founding_artist_agreement', 'PlotArt Founding Artist Agreement', 'fixed',
  '62adedbf330a0f6d02e952c7f4f7bfc9232696103dd10d52fa72b99a88693463', 'cc3294340834db30c14c47cb811042d91e3619e73aca3dfd2fafc032d8bd8011',
  strftime('%Y-%m-%dT%H:%M:%SZ','now'), strftime('%Y-%m-%dT%H:%M:%SZ','now'));

-- 6 · Carry across ONLY the licence acceptances the Studio already holds (artists.licence_version / licence_accepted_at),
--     exactly as recorded. Nothing is invented and no text is attributed: method migrated, label only, no fingerprint, no
--     email (the address at that moment was not recorded). The statement is the checkbox wording Studio has shown since
--     29 Oct 2026. The table's checks make it impossible for this step (or anything else) to create a migrated row for
--     any document other than PA-GPIL-2026-10-29. No Founding Artist Agreement acceptance is created for anyone.
INSERT INTO agreement_acceptances (id, event_id, artist_id, doc_id, doc_sha256, pdf_sha256, accepted_at, account_email, display_name, legal_name,
                                   method, statement, note, created_at)
SELECT 'acc-mig-' || a.id, 'evt-mig-' || a.id, a.id, a.licence_version, NULL, NULL, a.licence_accepted_at, NULL, a.display_name, NULL,
       'migrated_from_artists_table',
       'I approve my PlotArt gallery preview and accept the Gallery Publication and Image Licence, version ' || a.licence_version || '.',
       'Copied by migration 0005 from artists.licence_version and licence_accepted_at. Studio showed a one-sentence summary and this version label; no fixed full text existed for this version, and none is attributed.',
       strftime('%Y-%m-%dT%H:%M:%SZ','now')
FROM artists a
WHERE a.licence_version = 'PA-GPIL-2026-10-29' AND a.licence_accepted_at IS NOT NULL;

-- 6b · The enquiry log from enquiries the relay ALREADY holds (real rows only; no buyer details copied). Every relay enquiry
--      is in the artist's Studio Enquiries list from the moment it arrives, so each counts as introduced then.
--      Founding: Founding Artists only; before first publication, or before first publication + 12 months. The Studio
--      applies the exact Irish-date rule from now on; for an existing row this bound can only be later than the exact
--      rule's end (never earlier), so no enquiry is ever wrongly marked as outside the founding year.
INSERT INTO enquiry_log (id, reference, artist_id, artwork_id, route, introduced_at, founding, founding_year_end, logged_by, logged_at, late_entry, corrects, note)
SELECT 'enq-mig-' || e.id, e.reference, e.artist_id, e.artwork_id, 'relay', e.created_at,
       CASE WHEN a.founding = 1 AND (a.first_published_at IS NULL OR e.created_at < strftime('%Y-%m-%dT%H:%M:%SZ', a.first_published_at, '+12 months')) THEN 1 ELSE 0 END,
       CASE WHEN a.founding = 1 AND a.first_published_at IS NOT NULL THEN date(a.first_published_at, '+12 months', '-1 day') END,
       'migration 0005', strftime('%Y-%m-%dT%H:%M:%SZ','now'), 0, NULL, NULL
FROM enquiries e JOIN artists a ON a.id = e.artist_id;

-- 7 · Verification (read-only; run before and after, and compare):
-- SELECT COUNT(*) FROM artists;                                                                    -- unchanged
-- SELECT id, licence_version, licence_accepted_at, first_published_at FROM artists;                -- unchanged, row for row
-- SELECT COUNT(*) FROM enquiries;                                                                  -- unchanged
-- SELECT COUNT(*) FROM artists WHERE licence_version = 'PA-GPIL-2026-10-29' AND licence_accepted_at IS NOT NULL;
-- SELECT COUNT(*) FROM agreement_acceptances WHERE method = 'migrated_from_artists_table';           -- equals the line above
-- SELECT COUNT(*) FROM agreement_acceptances WHERE doc_id IN ('PA-FAA-2026-11','PA-GPIL-2026-11');   -- 0
-- SELECT COUNT(*) FROM enquiry_log;                                                                -- equals SELECT COUNT(*) FROM enquiries
-- SELECT doc_id, text_status, html_sha256, pdf_sha256 FROM agreement_documents;                    -- 3 rows, as section 5
-- Rollback (only before the first real acceptance; drops ONLY what this migration created; every line is IF EXISTS, so it
-- also cleans up after a run that stopped part-way):
--   DROP TRIGGER IF EXISTS agreement_acceptances_valid; DROP TRIGGER IF EXISTS agreement_acceptances_no_update; DROP TRIGGER IF EXISTS agreement_acceptances_no_delete;
--   DROP TRIGGER IF EXISTS enquiry_log_no_update; DROP TRIGGER IF EXISTS enquiry_log_no_delete;
--   DROP TRIGGER IF EXISTS acceptance_corrections_valid; DROP TRIGGER IF EXISTS acceptance_corrections_no_update; DROP TRIGGER IF EXISTS acceptance_corrections_no_delete;
--   DROP TRIGGER IF EXISTS participation_events_one_ending; DROP TRIGGER IF EXISTS participation_events_no_update; DROP TRIGGER IF EXISTS participation_events_no_delete;
--   DROP TRIGGER IF EXISTS record_retention_no_update; DROP TRIGGER IF EXISTS record_retention_no_delete;
--   DROP TRIGGER IF EXISTS agreement_documents_no_update; DROP TRIGGER IF EXISTS agreement_documents_no_delete;
--   DROP TABLE IF EXISTS acceptance_corrections; DROP TABLE IF EXISTS participation_events; DROP TABLE IF EXISTS agreement_acceptances;
--   DROP TABLE IF EXISTS enquiry_log; DROP TABLE IF EXISTS record_retention; DROP TABLE IF EXISTS agreement_documents;
