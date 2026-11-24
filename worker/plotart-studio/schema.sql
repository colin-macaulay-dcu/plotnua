-- PlotArt Studio · D1 schema (Phase 2, 29 Oct 2026). NOT CREATED IN PRODUCTION: local tests only until approved.
-- Working copy (artists, artworks, images) is what the artist edits. versions holds every approved or instant
-- snapshot; the newest one is what is live (or about to be). Nothing here is public until the publishing
-- pipeline turns an approved version into gallery pages through the Phase 1 safeguards.

CREATE TABLE IF NOT EXISTS artists (
  id TEXT PRIMARY KEY,
  slug TEXT NOT NULL UNIQUE,
  email TEXT NOT NULL UNIQUE COLLATE NOCASE,
  display_name TEXT NOT NULL,
  founding INTEGER NOT NULL DEFAULT 1,
  practice TEXT, medium TEXT, county TEXT,
  county_public INTEGER NOT NULL DEFAULT 0,
  statement TEXT, bio TEXT, website TEXT, instagram TEXT,
  portrait_image_id TEXT,
  account_status TEXT NOT NULL DEFAULT 'invited' CHECK (account_status IN ('invited','active','suspended','ended')),
  licence_version TEXT, licence_accepted_at TEXT,
  first_published_at TEXT,
  below_min_since TEXT,             -- a Founding gallery fell below 10 works: 30-day top-up from this date
  application_ref TEXT,
  created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
  founding_number INTEGER CHECK (founding_number IS NULL OR founding_number BETWEEN 1 AND 25)   -- permanent Founding 25 number (founder only)
);

CREATE TABLE IF NOT EXISTS artworks (
  id TEXT PRIMARY KEY,
  artist_id TEXT NOT NULL REFERENCES artists(id),
  slug TEXT NOT NULL,
  title TEXT, year INTEGER, medium TEXT, materials TEXT,
  h_cm REAL, w_cm REAL, d_cm REAL,
  price_eur INTEGER, price_on_request INTEGER NOT NULL DEFAULT 0,
  availability TEXT NOT NULL DEFAULT 'available' CHECK (availability IN ('available','reserved','sold','not_for_sale')),
  description TEXT,
  ord INTEGER NOT NULL,
  ai_involvement TEXT CHECK (ai_involvement IS NULL OR ai_involvement IN ('none','assisted','generated')),
  ai_note TEXT,
  archived INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
  UNIQUE (artist_id, slug)
);

CREATE TABLE IF NOT EXISTS images (
  id TEXT PRIMARY KEY,
  artist_id TEXT NOT NULL REFERENCES artists(id),
  artwork_id TEXT,
  role TEXT NOT NULL CHECK (role IN ('main','view','portrait')),
  r2_key TEXT NOT NULL,
  preview_key TEXT,
  sha256 TEXT NOT NULL,
  bytes INTEGER NOT NULL, width INTEGER NOT NULL, height INTEGER NOT NULL, format TEXT NOT NULL,
  alt TEXT, photographer TEXT CHECK (photographer IS NULL OR photographer IN ('self','other_with_permission')), photo_credit TEXT,
  checks TEXT NOT NULL,
  ord INTEGER NOT NULL DEFAULT 0,
  created_at TEXT NOT NULL, deleted_at TEXT
);
CREATE INDEX IF NOT EXISTS images_sha ON images (sha256);

CREATE TABLE IF NOT EXISTS submissions (
  id TEXT PRIMARY KEY,
  artist_id TEXT NOT NULL REFERENCES artists(id),
  created_at TEXT NOT NULL,
  tier TEXT NOT NULL CHECK (tier IN ('light','full')),
  status TEXT NOT NULL CHECK (status IN ('pending','approved','changes_requested','declined','withdrawn')),
  note TEXT, founder_message TEXT, decided_at TEXT,
  snapshot TEXT NOT NULL, changes TEXT NOT NULL, base_version INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS versions (
  artist_id TEXT NOT NULL REFERENCES artists(id),
  version INTEGER NOT NULL,
  snapshot TEXT NOT NULL,
  source TEXT NOT NULL,             -- submission id, 'instant', 'restore:<n>' or 'unpublish'
  created_at TEXT NOT NULL,
  ai_decisions TEXT,
  PRIMARY KEY (artist_id, version)
);

CREATE TABLE IF NOT EXISTS publish_queue (
  id TEXT PRIMARY KEY,
  artist_id TEXT NOT NULL REFERENCES artists(id),
  version INTEGER NOT NULL,
  kind TEXT NOT NULL CHECK (kind IN ('reviewed','instant','remove')),
  status TEXT NOT NULL CHECK (status IN ('awaiting_founder','ready','exporting','published','failed','superseded')),
  created_at TEXT NOT NULL, updated_at TEXT NOT NULL, detail TEXT
);

CREATE TABLE IF NOT EXISTS audit (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  at TEXT NOT NULL, actor TEXT NOT NULL, role TEXT NOT NULL,
  action TEXT NOT NULL, artist_id TEXT, detail TEXT
);

-- Buyer-to-artist enquiries (Phase 3). Written by the public enquiry Worker (src/enquiry.js); read by the artist it is
-- for and by the founder. Kept 24 months (privacy notice V8), then deleted by the Studio's daily clean-up.
CREATE TABLE IF NOT EXISTS enquiries (
  id TEXT PRIMARY KEY,
  reference TEXT NOT NULL UNIQUE,
  artist_id TEXT NOT NULL REFERENCES artists(id),
  artwork_id TEXT, artwork_title TEXT,
  buyer_name TEXT NOT NULL, buyer_email TEXT NOT NULL, message TEXT NOT NULL,
  notice_version TEXT NOT NULL,
  created_at TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('received','sent','send_failed')),
  sent_at TEXT, detail TEXT,
  delete_after TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS enquiries_artist ON enquiries (artist_id, created_at);


-- Gallery order (founder decision 31 Oct 2026). The founder's positions 01-25 in the public Virtual Gallery: a row holds
-- either an artist or a reservation. A reservation's note is private (founder only) and is never exported.
-- Display order only: an artist's permanent Founding 25 number is artists.founding_number and never changes with it.
CREATE TABLE IF NOT EXISTS gallery_positions (
  position INTEGER PRIMARY KEY CHECK (position BETWEEN 1 AND 25),
  artist_id TEXT UNIQUE REFERENCES artists(id),
  reserved INTEGER NOT NULL DEFAULT 0 CHECK (reserved IN (0, 1)),
  note TEXT,
  updated_at TEXT NOT NULL,
  CHECK ((reserved = 1 AND artist_id IS NULL) OR (reserved = 0 AND artist_id IS NOT NULL AND note IS NULL))
);
CREATE UNIQUE INDEX IF NOT EXISTS artists_founding_number ON artists(founding_number) WHERE founding_number IS NOT NULL;

-- PlotNua Idea Board (migration 0003, 1 Nov 2026): the same two tables, for new installs and local tests.
CREATE TABLE ideas (
  id TEXT PRIMARY KEY,
  ref TEXT NOT NULL UNIQUE,
  text TEXT NOT NULL CHECK (length(text) BETWEEN 8 AND 160),
  public_text TEXT CHECK (public_text IS NULL OR length(public_text) BETWEEN 8 AND 160),
  area TEXT CHECK (area IS NULL OR area IN ('Space', 'Garden', 'Art', 'Energy', 'Frontage', 'Neighbourhood', 'Income')),
  county TEXT CHECK (county IS NULL OR length(county) BETWEEN 3 AND 20),
  show_county INTEGER NOT NULL DEFAULT 0 CHECK (show_county IN (0, 1)),
  status TEXT NOT NULL DEFAULT 'received' CHECK (status IN ('received', 'approved', 'not_approved', 'removed')),
  became_discovery TEXT CHECK (became_discovery IS NULL OR became_discovery GLOB 'discovery-[a-z0-9]*.html'),
  edited INTEGER NOT NULL DEFAULT 0 CHECK (edited IN (0, 1)),
  created_at TEXT NOT NULL,
  decided_at TEXT,
  decided_by TEXT,
  published_at TEXT,
  removed_at TEXT,
  CHECK (show_county = 0 OR county IS NOT NULL)
);
CREATE INDEX ideas_status_published ON ideas(status, published_at);
-- Daily intake counter (the daily cap). One row per UTC day; holds a number only.
CREATE TABLE idea_intake_days (
  day TEXT PRIMARY KEY,
  n INTEGER NOT NULL DEFAULT 0
);

-- The Borrowed Garden noticeboard (migration 0004, 4 Nov 2026): the same tables, for new installs and local tests.
CREATE TABLE garden_listings (
  id TEXT PRIMARY KEY,
  ref TEXT NOT NULL UNIQUE,
  kind TEXT NOT NULL CHECK (kind IN ('have', 'want')),
  county TEXT NOT NULL CHECK (length(county) BETWEEN 3 AND 20),
  area TEXT NOT NULL CHECK (length(area) BETWEEN 2 AND 40),
  space_type TEXT NOT NULL CHECK (space_type IN ('raised_beds', 'vegetable_patch', 'lawn', 'greenhouse', 'orchard', 'flexible')),
  availability TEXT NOT NULL CHECK (availability IN ('now', 'this_season', 'next_season', 'flexible')),
  description TEXT NOT NULL CHECK (length(description) BETWEEN 20 AND 400),
  public_text TEXT CHECK (public_text IS NULL OR length(public_text) BETWEEN 20 AND 400),
  photo_key TEXT,
  contact_email TEXT NOT NULL CHECK (length(contact_email) BETWEEN 6 AND 120),
  consent_at TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'received' CHECK (status IN ('received', 'approved', 'rejected', 'removed', 'expired')),
  edited INTEGER NOT NULL DEFAULT 0 CHECK (edited IN (0, 1)),
  created_at TEXT NOT NULL,
  decided_at TEXT,
  decided_by TEXT,
  published_at TEXT,
  expires_at TEXT,
  removed_at TEXT,
  account_type TEXT NOT NULL DEFAULT 'individual' CHECK (account_type IN ('individual', 'organisation')),
  listing_tier TEXT NOT NULL DEFAULT 'free' CHECK (listing_tier IN ('free', 'premium')),
  featured_until TEXT,
  organisation_id TEXT,
  CHECK (status <> 'approved' OR (published_at IS NOT NULL AND expires_at IS NOT NULL))
);
CREATE INDEX garden_listings_status_published ON garden_listings(status, published_at);
CREATE INDEX garden_listings_county ON garden_listings(county, status);
-- Daily intake counter (the daily cap). One row per UTC day; holds a number only.
CREATE TABLE garden_intake_days (
  day TEXT PRIMARY KEY,
  n INTEGER NOT NULL DEFAULT 0
);
-- Enquiry relay record (prepared, NOT switched on): a reference, the listing and the time. The message itself is
-- e-mailed and never stored; neither person's address is stored here.
CREATE TABLE garden_enquiries (
  id TEXT PRIMARY KEY,
  ref TEXT NOT NULL UNIQUE,
  listing_id TEXT NOT NULL,
  created_at TEXT NOT NULL
);
CREATE TABLE garden_enquiry_days (
  day TEXT NOT NULL,
  listing_id TEXT NOT NULL,
  n INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY (day, listing_id)
);

-- Founding Artist Agreement acceptance records and the enquiry log (migration 0005, development 6 Nov 2026): the same
-- tables, triggers and document rows, for new installs and local tests. Kept identical to the migration by test/prove-migration-0005.mjs.
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
INSERT INTO agreement_documents (doc_id, kind, title, text_status, html_sha256, pdf_sha256, effective_at, created_at) VALUES
 ('PA-GPIL-2026-10-29', 'gallery_licence', 'PlotArt Gallery Publication and Image Licence', 'label_only', NULL, NULL,
  '2026-10-29T00:00:00Z', strftime('%Y-%m-%dT%H:%M:%SZ','now')),
 ('PA-GPIL-2026-11', 'gallery_licence', 'PlotArt Gallery Publication and Image Licence', 'fixed',
  'f4a2c72e8068a267afac87a7555ac509fb64d9b9a9385f389a855d5ba8408f92', 'aa3c27423f21877006bac7bd5e3132111dea5e2914617cf30826b4203637ba17',
  strftime('%Y-%m-%dT%H:%M:%SZ','now'), strftime('%Y-%m-%dT%H:%M:%SZ','now')),
 ('PA-FAA-2026-11', 'founding_artist_agreement', 'PlotArt Founding Artist Agreement', 'fixed',
  '62adedbf330a0f6d02e952c7f4f7bfc9232696103dd10d52fa72b99a88693463', 'cc3294340834db30c14c47cb811042d91e3619e73aca3dfd2fafc032d8bd8011',
  strftime('%Y-%m-%dT%H:%M:%SZ','now'), strftime('%Y-%m-%dT%H:%M:%SZ','now'));

-- Art for Hire tables (migration 0007, file 0007_art_for_hire.sql, development 10 Nov 2026): the same tables, indexes and guards, for new installs and
-- local tests. Kept identical to the migration by test/prove-migration-0007.mjs.

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

-- Art for Hire hire reports (migration 0008, file 0008_hire_reports.sql, development 11 Nov 2026): the same tables, indexes and guards,
-- for new installs and local tests. Kept identical to the migration by test/prove-migration-0008.mjs.

-- 1 · An artist's report of a successful hire (r5 clause 6.5). Append-only: a mistake is corrected by a NEW report that
--     names the one it corrects. The commission basis and amount are fixed when the report is made, from the enquiry log's
--     founding flag (fixed at introduction, clause 6.3) and the 12-month window measured from the introduction to the date
--     the hire was AGREED (clause 6.2(c)). A hire period starting before the introduction is flagged for the founder.
CREATE TABLE IF NOT EXISTS hire_reports (
  id               TEXT PRIMARY KEY,
  artist_id        TEXT NOT NULL,                     -- artists.id (no foreign key: see the header)
  reference        TEXT NOT NULL,                     -- enquiry_log.reference: PA-H-... (relay) or PA-EM-... (logged email introduction)
  artwork_ids      TEXT NOT NULL CHECK (json_valid(artwork_ids) AND json_array_length(artwork_ids) BETWEEN 1 AND 20),
  hire_start       TEXT NOT NULL CHECK (hire_start GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'),
  hire_end         TEXT NOT NULL CHECK (hire_end GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]' AND hire_end >= hire_start),
  agreed_on        TEXT NOT NULL CHECK (agreed_on GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'),   -- the date the hire was agreed (clause 6.2(c))
  starts_before_introduction INTEGER NOT NULL CHECK (starts_before_introduction IN (0, 1)),            -- flagged for the founder, not refused
  net_fee_cents    INTEGER NOT NULL CHECK (net_fee_cents BETWEEN 0 AND 100000000),   -- excludes VAT and itemised expenses (6.2(d))
  more_to_pay      INTEGER NOT NULL CHECK (more_to_pay IN (0, 1)),                  -- an instalment: more of the fee is still due
  introduced_at    TEXT NOT NULL,                     -- copied from enquiry_log.introduced_at
  founding         INTEGER NOT NULL CHECK (founding IN (0, 1)),   -- copied from enquiry_log.founding (protected, 6.3)
  basis            TEXT NOT NULL CHECK (basis IN ('commission', 'founding_year', 'outside_window', 'no_fee')),
  rate_bp          INTEGER NOT NULL CHECK (rate_bp = 1000),       -- 10% in basis points (PA-AFH-2026-11 clause 6.1)
  commission_cents INTEGER NOT NULL CHECK (commission_cents >= 0 AND (basis = 'commission' OR commission_cents = 0)),
  terms_doc        TEXT NOT NULL,                     -- the PA-AFH identifier the artist had accepted when reporting
  corrects         TEXT REFERENCES hire_reports(id),
  reported_at      TEXT NOT NULL,
  reported_by      TEXT NOT NULL,                     -- the artist's Studio address
  CHECK (basis <> 'founding_year' OR founding = 1)
);
CREATE INDEX IF NOT EXISTS hire_reports_artist ON hire_reports(artist_id, reported_at);
CREATE INDEX IF NOT EXISTS hire_reports_reference ON hire_reports(reference);
CREATE TRIGGER IF NOT EXISTS hire_reports_no_update BEFORE UPDATE ON hire_reports
BEGIN SELECT RAISE(ABORT, 'hire_reports is append-only: report a correction instead'); END;
CREATE TRIGGER IF NOT EXISTS hire_reports_no_delete BEFORE DELETE ON hire_reports
WHEN NOT EXISTS (SELECT 1 FROM record_retention r WHERE r.artist_id = OLD.artist_id AND julianday(r.delete_after) <= julianday('now'))
BEGIN SELECT RAISE(ABORT, 'hire_reports is kept until its retention period has ended'); END;

-- 2 · The founder's own manual record for each report (r5 clauses 6.6 and 10.1): whether it has been invoiced and paid.
--     Editable by the founder only (every change audited); deleted with the report once retention has ended.
CREATE TABLE IF NOT EXISTS hire_report_records (
  report_id      TEXT PRIMARY KEY REFERENCES hire_reports(id),
  artist_id      TEXT NOT NULL,
  invoice_status TEXT NOT NULL DEFAULT 'not_invoiced' CHECK (invoice_status IN ('not_invoiced', 'invoiced', 'no_commission', 'disputed', 'superseded')),
  invoice_no     TEXT CHECK (invoice_no IS NULL OR length(invoice_no) BETWEEN 1 AND 40),
  invoiced_on    TEXT CHECK (invoiced_on IS NULL OR invoiced_on GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'),
  payment_status TEXT NOT NULL DEFAULT 'unpaid' CHECK (payment_status IN ('unpaid', 'paid', 'not_due', 'refunded')),
  paid_on        TEXT CHECK (paid_on IS NULL OR paid_on GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'),
  note           TEXT CHECK (note IS NULL OR length(note) <= 280),   -- private to the founder
  updated_at     TEXT NOT NULL,
  updated_by     TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS hire_report_records_artist ON hire_report_records(artist_id);
CREATE TRIGGER IF NOT EXISTS hire_report_records_no_delete BEFORE DELETE ON hire_report_records
WHEN NOT EXISTS (SELECT 1 FROM record_retention r WHERE r.artist_id = OLD.artist_id AND julianday(r.delete_after) <= julianday('now'))
BEGIN SELECT RAISE(ABORT, 'hire_report_records is kept until its retention period has ended'); END;

-- PlotArt Studio · migration 0009 · Opportunities & delivery (development 13 Nov 2026): the artist's own expression of interest.
CREATE TABLE IF NOT EXISTS artist_opportunities (
  artist_id         TEXT PRIMARY KEY REFERENCES artists(id) ON DELETE CASCADE,
  interests         TEXT NOT NULL CHECK (json_valid(interests) AND json_array_length(interests) BETWEEN 1 AND 8),   -- keys, e.g. ["living_gallery","commissions"]
  artwork_county    TEXT CHECK (artwork_county IS NULL OR length(artwork_county) BETWEEN 3 AND 20),               -- NULL: not answered
  transport         TEXT NOT NULL DEFAULT '[]' CHECK (json_valid(transport) AND json_array_length(transport) <= 4),
  coverage_mode     TEXT CHECK (coverage_mode IS NULL OR coverage_mode IN ('counties', 'anywhere', 'ask')),           -- NULL: not asked or not answered
  coverage_counties TEXT NOT NULL DEFAULT '[]' CHECK (json_valid(coverage_counties) AND json_array_length(coverage_counties) <= 32),
  note              TEXT CHECK (note IS NULL OR length(note) <= 280),
  created_at        TEXT NOT NULL,
  updated_at        TEXT NOT NULL,
  updated_by        TEXT NOT NULL,                                                                                 -- the artist's Studio address
  CHECK (NOT (interests LIKE '%"online_only"%' AND json_array_length(interests) > 1)),
  CHECK (NOT (interests LIKE '%"online_only"%' AND (json_array_length(transport) > 0 OR coverage_mode IS NOT NULL))),
  CHECK ((COALESCE(coverage_mode, '') = 'counties') = (json_array_length(coverage_counties) > 0))   -- counties only with "selected counties"
);
CREATE INDEX IF NOT EXISTS artist_opportunities_county ON artist_opportunities(artwork_county);

-- PlotArt Studio · migration 0010 · Opportunities & delivery: care condition and a 2,000-character practical note (development 13 Nov 2026).
ALTER TABLE artist_opportunities ADD COLUMN care_condition INTEGER NOT NULL DEFAULT 0 CHECK (care_condition IN (0, 1));
ALTER TABLE artist_opportunities ADD COLUMN practical_note TEXT CHECK (practical_note IS NULL OR length(practical_note) <= 2000);
UPDATE artist_opportunities SET practical_note = note WHERE note IS NOT NULL AND practical_note IS NULL;

-- PlotArt Studio · migration 0011 · Open for Commissions: the artist's own on/off switch (development 13 Nov 2026).
ALTER TABLE artists ADD COLUMN open_for_commissions INTEGER NOT NULL DEFAULT 0 CHECK (open_for_commissions IN (0, 1));

-- PlotArt Studio · migration 0012 · Gallery Artist terms and agreement records (development 13 Nov 2026).
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

-- Gallery application review (migration 0014).
-- Gallery applications only. No existing application/artist rows are changed.
CREATE TABLE IF NOT EXISTS application_review (
  ref TEXT PRIMARY KEY,
  revision INTEGER NOT NULL DEFAULT 0,
  token_hash TEXT,
  token_expires TEXT,
  requested_message TEXT,
  active_action TEXT,
  active_since TEXT,
  revised_at TEXT
);
CREATE TABLE IF NOT EXISTS application_review_actions (
  id TEXT PRIMARY KEY,
  ref TEXT NOT NULL,
  kind TEXT NOT NULL,
  actor TEXT NOT NULL,
  payload TEXT NOT NULL,
  phase TEXT NOT NULL DEFAULT 'prepared',
  running_at TEXT,
  created_at TEXT NOT NULL,
  sent_at TEXT,
  completed_at TEXT,
  error TEXT,
  FOREIGN KEY(ref) REFERENCES application_review(ref) ON DELETE CASCADE
);
CREATE INDEX IF NOT EXISTS application_review_actions_ref ON application_review_actions(ref,created_at);

-- PlotArt Studio · migration 0015 · Opportunities shown publicly: the artist's own choice (development 16 Nov 2026).
ALTER TABLE artist_opportunities ADD COLUMN public_display INTEGER CHECK (public_display IS NULL OR public_display IN (0, 1));
ALTER TABLE artist_opportunities ADD COLUMN public_decided_at TEXT CHECK (public_decided_at IS NULL OR length(public_decided_at) BETWEEN 20 AND 30);
ALTER TABLE artist_opportunities ADD COLUMN public_notice TEXT CHECK (public_notice IS NULL OR length(public_notice) BETWEEN 8 AND 40);

-- PlotArt Studio · migration 0016 · Homepage curation: the founder's featured artworks and artists (development 17 Nov 2026).
CREATE TABLE IF NOT EXISTS homepage_features (
  position INTEGER PRIMARY KEY CHECK (position BETWEEN 1 AND 6),
  kind TEXT NOT NULL CHECK (kind IN ('artwork', 'artist')),
  artist_id TEXT NOT NULL REFERENCES artists(id),
  artwork_id TEXT NOT NULL REFERENCES artworks(id),
  updated_at TEXT NOT NULL CHECK (length(updated_at) BETWEEN 20 AND 30)
);

-- PlotArt Studio · migration 0017 · Managed checkout pilot (development 16 Nov 2026). NOT APPLIED IN PRODUCTION.
-- New tables only. No existing table, row, agreement, acceptance, gallery position or publishing record is changed.
-- Triggers are refusal-only BEFORE triggers on these NEW tables (migration-check policy, 6 Nov 2026): this migration
-- needs the founder's explicit approval of this exact file, and both production backups, before it runs.
-- Test mode only: every provider-facing table carries livemode = 0 by CHECK.
-- No foreign keys to artists/artworks: order and accounting records follow their own retention, and never block the
-- existing participation-deletion schedule.

-- 1 · Installed pilot texts: the artist payment addendum and the buyer purchase terms. A text is accepted only when the
--     same fingerprint is bundled with the Workers (src/payment-terms.js). Rows never change: a new text gets a new id.
CREATE TABLE IF NOT EXISTS payment_terms (
  doc_id       TEXT PRIMARY KEY,
  kind         TEXT NOT NULL CHECK (kind IN ('artist_payment_addendum', 'buyer_purchase_terms')),
  title        TEXT NOT NULL,
  html_sha256  TEXT NOT NULL CHECK (length(html_sha256) = 64),
  effective_at TEXT NOT NULL,
  created_at   TEXT NOT NULL
);
CREATE TRIGGER IF NOT EXISTS payment_terms_no_update BEFORE UPDATE ON payment_terms
BEGIN SELECT RAISE(ABORT, 'payment_terms rows never change: install a new identifier'); END;
CREATE TRIGGER IF NOT EXISTS payment_terms_no_delete BEFORE DELETE ON payment_terms
BEGIN SELECT RAISE(ABORT, 'payment_terms rows are never removed'); END;

-- 2 · Explicit artist opt-in and opt-out, append-only. The latest row decides. Joining needs the artist's own tick on
--     the installed addendum; nobody is enrolled by the founder or by default. The SEPARATE consent to Stripe's processing
--     charge on commission-free orders ('processing_consent' / '..._withdrawn') is recorded here too, with its statement.
CREATE TABLE IF NOT EXISTS payment_pilot_events (
  id            TEXT PRIMARY KEY,
  artist_id     TEXT NOT NULL,
  kind          TEXT NOT NULL CHECK (kind IN ('opted_in', 'left', 'processing_consent', 'processing_consent_withdrawn')),
  doc_id        TEXT REFERENCES payment_terms(doc_id),
  doc_sha256    TEXT,
  account_email TEXT NOT NULL,
  display_name  TEXT,
  statement     TEXT,
  at            TEXT NOT NULL,
  CHECK (kind IN ('left', 'processing_consent_withdrawn')
    OR (kind = 'opted_in' AND doc_id IS NOT NULL AND length(doc_sha256) = 64 AND statement IS NOT NULL AND display_name IS NOT NULL)
    OR (kind = 'processing_consent' AND doc_id IS NULL AND statement IS NOT NULL AND display_name IS NOT NULL))
);
CREATE INDEX IF NOT EXISTS payment_pilot_events_artist ON payment_pilot_events(artist_id, at);
CREATE TRIGGER IF NOT EXISTS payment_pilot_events_valid BEFORE INSERT ON payment_pilot_events
WHEN NEW.kind = 'opted_in' AND NOT EXISTS (SELECT 1 FROM payment_terms t WHERE t.doc_id = NEW.doc_id AND t.kind = 'artist_payment_addendum'
  AND t.html_sha256 = NEW.doc_sha256 AND julianday(NEW.at) >= julianday(t.effective_at))
BEGIN SELECT RAISE(ABORT, 'opt-in refused: not an installed addendum, wrong fingerprint, or dated before it took effect'); END;
CREATE TRIGGER IF NOT EXISTS payment_pilot_events_no_update BEFORE UPDATE ON payment_pilot_events
BEGIN SELECT RAISE(ABORT, 'payment_pilot_events is append-only'); END;
-- deletable only six years after the artist LEFT the pilot, and only once none of their orders is still kept
CREATE TRIGGER IF NOT EXISTS payment_pilot_events_no_delete BEFORE DELETE ON payment_pilot_events
WHEN EXISTS (SELECT 1 FROM checkout_orders o WHERE o.artist_id = OLD.artist_id)
  OR NOT EXISTS (SELECT 1 FROM payment_pilot_events e WHERE e.artist_id = OLD.artist_id AND e.kind = 'left' AND julianday(e.at) <= julianday('now', '-6 years')
    AND e.at = (SELECT MAX(x.at) FROM payment_pilot_events x WHERE x.artist_id = OLD.artist_id))
BEGIN SELECT RAISE(ABORT, 'payment_pilot_events is kept until six years after the artist left and their orders are gone'); END;

-- 3 · The artist's own Stripe account (identity documents stay with Stripe's hosted onboarding; none are stored here).
CREATE TABLE IF NOT EXISTS payment_accounts (
  artist_id         TEXT PRIMARY KEY,
  provider          TEXT NOT NULL DEFAULT 'stripe' CHECK (provider = 'stripe'),
  account_id        TEXT NOT NULL UNIQUE CHECK (account_id GLOB 'acct_*'),
  country           TEXT NOT NULL CHECK (country IN ('IE', 'GB')),
  livemode          INTEGER NOT NULL DEFAULT 0 CHECK (livemode = 0),
  charges_enabled   INTEGER NOT NULL DEFAULT 0 CHECK (charges_enabled IN (0, 1)),
  payouts_enabled   INTEGER NOT NULL DEFAULT 0 CHECK (payouts_enabled IN (0, 1)),
  details_submitted INTEGER NOT NULL DEFAULT 0 CHECK (details_submitted IN (0, 1)),
  requirements_due  TEXT,
  checked_at        TEXT,
  created_at        TEXT NOT NULL,
  updated_at        TEXT NOT NULL
);

-- 4 · Orders: one artist, one unique original, EUR, integer cents. Money and entitlement are snapshotted when quoted.
CREATE TABLE IF NOT EXISTS checkout_orders (
  id                 TEXT PRIMARY KEY,
  reference          TEXT NOT NULL UNIQUE CHECK (reference GLOB 'PA-O-*'),
  artist_id          TEXT NOT NULL,
  artwork_id         TEXT NOT NULL,
  enquiry_ref        TEXT NOT NULL,
  status             TEXT NOT NULL CHECK (status IN ('draft','awaiting_artist','quoted','checkout_open','paid','dispatched','delivered','closed',
                                                      'expired','cancelled','payment_failed','refund_pending','refunded','disputed')),
  payment_status     TEXT NOT NULL DEFAULT 'none' CHECK (payment_status IN ('none','open','paid','failed','partially_refunded','refunded')),
  fulfilment_status  TEXT NOT NULL DEFAULT 'none' CHECK (fulfilment_status IN ('none','dispatched','delivered')),
  dispute_status     TEXT NOT NULL DEFAULT 'none' CHECK (dispute_status IN ('none','open','won','lost')),
  needs_resolution   TEXT,                                   -- set when a payment arrives that cannot complete a sale (e.g. already sold)
  processing         TEXT,                                   -- JSON (Model B): Stripe's actual processing fee + VAT on it, what PlotArt reimbursed, any shortfall owed outside Stripe
  dispute_fees       TEXT,                                   -- JSON: per dispute, whether Stripe supplied its fee lines ('recorded') or not ('unavailable')
  quote_sha256       TEXT,                                   -- fingerprint of the issued quote snapshot (quote_snapshots)
  currency           TEXT NOT NULL DEFAULT 'eur' CHECK (currency = 'eur'),
  artwork_cents      INTEGER CHECK (artwork_cents IS NULL OR artwork_cents BETWEEN 100 AND 999999),
  delivery_cents     INTEGER CHECK (delivery_cents IS NULL OR delivery_cents BETWEEN 0 AND 200000),
  commission_bp      INTEGER CHECK (commission_bp IS NULL OR commission_bp BETWEEN 0 AND 1500),
  commission_cents   INTEGER,
  commission_basis   TEXT,
  entitlement        TEXT,                                   -- JSON evidence for the commission decision
  exclusion          TEXT,
  negotiation_note   TEXT CHECK (negotiation_note IS NULL OR length(negotiation_note) <= 1000),
  delivery           TEXT,                                   -- JSON: packing, transport, cover, receipt, returns (rules.cleanDelivery)
  artwork_snapshot   TEXT,                                   -- JSON: title, dimensions, medium as quoted
  seller             TEXT,                                   -- JSON: the seller's identity as shown to the buyer
  quote_version      INTEGER NOT NULL DEFAULT 1,
  artist_approved_version INTEGER,
  artist_approved_at TEXT,
  artist_confirmations TEXT,                                 -- JSON: availability, location, condition, framing, dimensions, packing
  quote_issued_at    TEXT,
  quote_expires_at   TEXT,
  addendum_doc_id    TEXT,
  buyer_terms_doc_id TEXT,
  buyer_terms_accepted_at TEXT,
  buyer_token_hash   TEXT UNIQUE,
  buyer_email        TEXT,
  provider_account   TEXT,
  payment_intent     TEXT UNIQUE,
  charge_id          TEXT UNIQUE,
  application_fee_id TEXT,
  amount_received_cents INTEGER,
  paid_at            TEXT,
  linked_order_check TEXT,                                   -- JSON: linked-order safeguard result and founder's confirmation (operational only; not an AML assessment)
  retain_until       TEXT,                                   -- fixed when the order ends: 31 Dec of the 6th year after the last money movement, or +2 years if none
  livemode           INTEGER NOT NULL DEFAULT 0 CHECK (livemode = 0),
  created_by         TEXT NOT NULL,
  created_at         TEXT NOT NULL,
  updated_at         TEXT NOT NULL,
  CHECK (commission_cents IS NULL OR (commission_cents >= 0 AND commission_cents <= artwork_cents))
);
CREATE INDEX IF NOT EXISTS checkout_orders_artist ON checkout_orders(artist_id, created_at);
CREATE INDEX IF NOT EXISTS checkout_orders_artwork ON checkout_orders(artwork_id);
CREATE INDEX IF NOT EXISTS checkout_orders_buyer ON checkout_orders(buyer_email COLLATE NOCASE, created_at);
CREATE TRIGGER IF NOT EXISTS checkout_orders_no_delete BEFORE DELETE ON checkout_orders
WHEN OLD.retain_until IS NULL OR julianday(OLD.retain_until) > julianday('now')
  OR EXISTS (SELECT 1 FROM checkout_holds h WHERE h.order_id = OLD.id AND h.released_at IS NULL)
  OR OLD.dispute_status = 'open'
BEGIN SELECT RAISE(ABORT, 'an order is kept until its retention period has ended, no legal hold is active and no dispute is open'); END;
-- a retention date is fixed once set: never shortened, never extended (keeping records longer is done by a reviewed hold)
CREATE TRIGGER IF NOT EXISTS checkout_orders_retention_fixed BEFORE UPDATE OF retain_until ON checkout_orders
WHEN OLD.retain_until IS NOT NULL AND (NEW.retain_until IS NULL OR NEW.retain_until <> OLD.retain_until)
BEGIN SELECT RAISE(ABORT, 'a retention date is fixed once set; place a reviewed legal hold instead'); END;

-- 5 · One reservation per original, with an explicit expiry. The PRIMARY KEY is what stops two checkouts at once.
CREATE TABLE IF NOT EXISTS artwork_reservations (
  artwork_id    TEXT PRIMARY KEY,
  order_id      TEXT NOT NULL UNIQUE REFERENCES checkout_orders(id),
  quote_version INTEGER NOT NULL,
  expires_at    TEXT NOT NULL,
  created_at    TEXT NOT NULL
);

-- 6 · One sale per original. The partial unique index makes a second concurrent sale impossible at the database.
CREATE TABLE IF NOT EXISTS artwork_sales (
  order_id    TEXT PRIMARY KEY REFERENCES checkout_orders(id),
  artwork_id  TEXT NOT NULL,
  sold_at     TEXT NOT NULL,
  released_at TEXT,
  released_reason TEXT
);
CREATE UNIQUE INDEX IF NOT EXISTS artwork_sales_one_active ON artwork_sales(artwork_id) WHERE released_at IS NULL;
CREATE TRIGGER IF NOT EXISTS artwork_sales_no_delete BEFORE DELETE ON artwork_sales
WHEN NOT (EXISTS (SELECT 1 FROM checkout_orders o WHERE o.id = OLD.order_id AND o.retain_until IS NOT NULL AND julianday(o.retain_until) <= julianday('now'))
  AND NOT EXISTS (SELECT 1 FROM checkout_holds h WHERE h.order_id = OLD.order_id AND h.released_at IS NULL))
BEGIN SELECT RAISE(ABORT, 'artwork_sales rows are kept with their order (retention and legal holds); release them with a reason'); END;

-- 7 · Hosted checkout sessions. At most one open session per order; a revised quote supersedes it first.
CREATE TABLE IF NOT EXISTS checkout_sessions (
  id              TEXT PRIMARY KEY CHECK (id GLOB 'cs_test_*'),
  order_id        TEXT NOT NULL REFERENCES checkout_orders(id),
  quote_version   INTEGER NOT NULL,
  amount_total    INTEGER NOT NULL,
  application_fee_cents INTEGER NOT NULL,
  status          TEXT NOT NULL CHECK (status IN ('open','complete','expired','superseded')),
  url             TEXT,
  expires_at      TEXT NOT NULL,
  created_at      TEXT NOT NULL,
  updated_at      TEXT NOT NULL
);
CREATE UNIQUE INDEX IF NOT EXISTS checkout_sessions_one_open ON checkout_sessions(order_id) WHERE status = 'open';

-- 8 · Verified provider events. The provider's event id is unique: a repeated delivery is recognised, never re-applied.
CREATE TABLE IF NOT EXISTS payment_events (
  event_id     TEXT PRIMARY KEY CHECK (event_id GLOB 'evt_*'),
  type         TEXT NOT NULL,
  account      TEXT,
  livemode     INTEGER NOT NULL CHECK (livemode = 0),
  created      INTEGER NOT NULL,
  object_id    TEXT,
  order_id     TEXT,
  status       TEXT NOT NULL CHECK (status IN ('received','processed','ignored','deferred','failed')),
  attempts     INTEGER NOT NULL DEFAULT 1,
  detail       TEXT,
  received_at  TEXT NOT NULL,
  processed_at TEXT
);

-- 9 · The money ledger, append-only. Positive = towards the party named by kind; refunds and disputes are negative.
--     (kind, provider_ref) is unique so a repeated event can never book the same movement twice.
CREATE TABLE IF NOT EXISTS order_ledger (
  id           TEXT PRIMARY KEY,
  order_id     TEXT NOT NULL REFERENCES checkout_orders(id),
  kind         TEXT NOT NULL CHECK (kind IN ('charge','commission','artist_artwork','delivery_allocation',
                 'artwork_refund','delivery_refund','artwork_refund_reversed','delivery_refund_reversed','commission_refund','processing_fee','processing_reimbursement','processing_shortfall_paid','dispute','dispute_reinstated','dispute_fee','dispute_fee_returned','external_refund','adjustment')),
  amount_cents INTEGER NOT NULL,
  provider_ref TEXT,
  at           TEXT NOT NULL,
  note         TEXT,
  UNIQUE (kind, provider_ref)
);
CREATE INDEX IF NOT EXISTS order_ledger_order ON order_ledger(order_id, at);
CREATE TRIGGER IF NOT EXISTS order_ledger_no_update BEFORE UPDATE ON order_ledger
BEGIN SELECT RAISE(ABORT, 'order_ledger is append-only; add an adjustment'); END;
CREATE TRIGGER IF NOT EXISTS order_ledger_no_delete BEFORE DELETE ON order_ledger
WHEN NOT (EXISTS (SELECT 1 FROM checkout_orders o WHERE o.id = OLD.order_id AND o.retain_until IS NOT NULL AND julianday(o.retain_until) <= julianday('now'))
  AND NOT EXISTS (SELECT 1 FROM checkout_holds h WHERE h.order_id = OLD.order_id AND h.released_at IS NULL))
BEGIN SELECT RAISE(ABORT, 'order_ledger is append-only until its order''s retention period has ended and no legal hold is active'); END;

-- 10 · Refunds requested by the founder (the artist, as seller, can also refund in their own Stripe Dashboard: those
--      arrive as provider events and are booked as external_refund for founder review).
CREATE TABLE IF NOT EXISTS order_refunds (
  id                  TEXT PRIMARY KEY,
  order_id            TEXT NOT NULL REFERENCES checkout_orders(id),
  artwork_cents       INTEGER NOT NULL CHECK (artwork_cents >= 0),
  delivery_cents      INTEGER NOT NULL CHECK (delivery_cents >= 0),
  commission_refund_cents INTEGER NOT NULL CHECK (commission_refund_cents >= 0),
  reason              TEXT NOT NULL CHECK (length(reason) BETWEEN 3 AND 500),
  status              TEXT NOT NULL CHECK (status IN ('pending','succeeded','failed')),
  provider_refund_id  TEXT UNIQUE,
  fee_refund_id       TEXT UNIQUE,
  error               TEXT,
  requested_by        TEXT NOT NULL,
  created_at          TEXT NOT NULL,
  updated_at          TEXT NOT NULL,
  CHECK (artwork_cents + delivery_cents > 0)
);

-- 11 · Fulfilment evidence, append-only: confirmations, dispatch, delivery, signed receipt, condition photographs.
CREATE TABLE IF NOT EXISTS order_fulfilment_events (
  id        TEXT PRIMARY KEY,
  order_id  TEXT NOT NULL REFERENCES checkout_orders(id),
  kind      TEXT NOT NULL CHECK (kind IN ('dispatched','delivered','signed_receipt','condition_photos','tracking','insurance','note')),
  actor     TEXT NOT NULL,
  at        TEXT NOT NULL,
  evidence  TEXT NOT NULL CHECK (length(evidence) BETWEEN 2 AND 2000)
);
CREATE TRIGGER IF NOT EXISTS order_fulfilment_events_no_update BEFORE UPDATE ON order_fulfilment_events
BEGIN SELECT RAISE(ABORT, 'order_fulfilment_events is append-only'); END;
CREATE TRIGGER IF NOT EXISTS order_fulfilment_events_no_delete BEFORE DELETE ON order_fulfilment_events
WHEN NOT (EXISTS (SELECT 1 FROM checkout_orders o WHERE o.id = OLD.order_id AND o.retain_until IS NOT NULL AND julianday(o.retain_until) <= julianday('now'))
  AND NOT EXISTS (SELECT 1 FROM checkout_holds h WHERE h.order_id = OLD.order_id AND h.released_at IS NULL))
BEGIN SELECT RAISE(ABORT, 'order_fulfilment_events is append-only until its order''s retention period has ended and no legal hold is active'); END;

-- 12 · Order audit: actor, action, time, prior and new status. Append-only.
CREATE TABLE IF NOT EXISTS order_events (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  order_id    TEXT NOT NULL REFERENCES checkout_orders(id),
  at          TEXT NOT NULL,
  actor       TEXT NOT NULL,
  action      TEXT NOT NULL,
  prior_status TEXT,
  new_status  TEXT,
  detail      TEXT
);
CREATE INDEX IF NOT EXISTS order_events_order ON order_events(order_id, id);
CREATE TRIGGER IF NOT EXISTS order_events_no_update BEFORE UPDATE ON order_events
BEGIN SELECT RAISE(ABORT, 'order_events is append-only'); END;
CREATE TRIGGER IF NOT EXISTS order_events_no_delete BEFORE DELETE ON order_events
WHEN NOT (EXISTS (SELECT 1 FROM checkout_orders o WHERE o.id = OLD.order_id AND o.retain_until IS NOT NULL AND julianday(o.retain_until) <= julianday('now'))
  AND NOT EXISTS (SELECT 1 FROM checkout_holds h WHERE h.order_id = OLD.order_id AND h.released_at IS NULL))
BEGIN SELECT RAISE(ABORT, 'order_events is append-only until its order''s retention period has ended and no legal hold is active'); END;

-- 13 · Legal holds: keep one order's records past its retention date for a stated reason, reviewed at least every 12
--      months, released with a reason. Only review_by can change (renewal) and released_* can be set once.
CREATE TABLE IF NOT EXISTS checkout_holds (
  id             TEXT PRIMARY KEY,
  order_id       TEXT NOT NULL REFERENCES checkout_orders(id),
  basis          TEXT NOT NULL CHECK (basis IN ('dispute','claim','revenue_enquiry','investigation','litigation','data_subject_request','other')),
  reason         TEXT NOT NULL CHECK (length(reason) BETWEEN 10 AND 1000),
  placed_by      TEXT NOT NULL,
  placed_at      TEXT NOT NULL,
  review_by      TEXT NOT NULL CHECK (review_by GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'),
  released_at    TEXT,
  released_by    TEXT,
  release_reason TEXT,
  CHECK ((released_at IS NULL) = (released_by IS NULL) AND (released_at IS NULL) = (release_reason IS NULL))
);
CREATE INDEX IF NOT EXISTS checkout_holds_order ON checkout_holds(order_id, released_at);
CREATE TRIGGER IF NOT EXISTS checkout_holds_limited_update BEFORE UPDATE ON checkout_holds
WHEN NEW.id <> OLD.id OR NEW.order_id <> OLD.order_id OR NEW.basis <> OLD.basis OR NEW.reason <> OLD.reason OR NEW.placed_by <> OLD.placed_by
  OR NEW.placed_at <> OLD.placed_at OR OLD.released_at IS NOT NULL
BEGIN SELECT RAISE(ABORT, 'a hold can only be renewed (new review date) or released once'); END;
CREATE TRIGGER IF NOT EXISTS checkout_holds_no_delete BEFORE DELETE ON checkout_holds
WHEN OLD.released_at IS NULL OR NOT EXISTS (SELECT 1 FROM checkout_orders o WHERE o.id = OLD.order_id AND o.retain_until IS NOT NULL AND julianday(o.retain_until) <= julianday('now'))
BEGIN SELECT RAISE(ABORT, 'a hold is deleted only after release, with its order, once retention has ended'); END;
CREATE TABLE IF NOT EXISTS checkout_hold_events (
  id        TEXT PRIMARY KEY,
  hold_id   TEXT NOT NULL REFERENCES checkout_holds(id),
  order_id  TEXT NOT NULL,
  kind      TEXT NOT NULL CHECK (kind IN ('placed','renewed','released')),
  actor     TEXT NOT NULL,
  at        TEXT NOT NULL,
  note      TEXT NOT NULL,
  review_by TEXT
);
CREATE TRIGGER IF NOT EXISTS checkout_hold_events_no_update BEFORE UPDATE ON checkout_hold_events
BEGIN SELECT RAISE(ABORT, 'checkout_hold_events is append-only'); END;
CREATE TRIGGER IF NOT EXISTS checkout_hold_events_no_delete BEFORE DELETE ON checkout_hold_events
WHEN EXISTS (SELECT 1 FROM checkout_holds h WHERE h.id = OLD.hold_id AND h.released_at IS NULL)
  OR NOT EXISTS (SELECT 1 FROM checkout_orders o WHERE o.id = OLD.order_id AND o.retain_until IS NOT NULL AND julianday(o.retain_until) <= julianday('now'))
BEGIN SELECT RAISE(ABORT, 'hold history is kept with its order'); END;

-- 13 · Seller information a buyer must have before paying (CRA 2022 Sch. 3; s.107). Kept by the artist in Studio while they
--      are in the pilot; each issued quote keeps its own copy (quote_snapshots), so later edits never change a quote.
CREATE TABLE IF NOT EXISTS seller_profiles (
  artist_id       TEXT PRIMARY KEY,
  legal_name      TEXT NOT NULL,
  trading_name    TEXT,
  address         TEXT NOT NULL,              -- geographical address at which the seller is established
  returns_address TEXT,                       -- if different: where returns and complaints go
  email           TEXT NOT NULL,
  phone           TEXT NOT NULL,
  trader_status   TEXT NOT NULL CHECK (trader_status IN ('trader','not_trader','unsure')),   -- managed checkout is open only to 'trader' (founder decision F2, Option A, 18 Nov 2026)
  vat_number      TEXT,
  declared_at     TEXT NOT NULL,
  declared_by     TEXT NOT NULL,
  updated_at      TEXT NOT NULL
);

-- 14 · The exact quote the buyer was shown, per issued version: append-only, fingerprinted, kept with its order.
CREATE TABLE IF NOT EXISTS quote_snapshots (
  order_id      TEXT NOT NULL REFERENCES checkout_orders(id),
  quote_version INTEGER NOT NULL,
  snapshot      TEXT NOT NULL,
  sha256        TEXT NOT NULL,
  issued_at     TEXT NOT NULL,
  PRIMARY KEY (order_id, quote_version)
);
CREATE TRIGGER IF NOT EXISTS quote_snapshots_no_update BEFORE UPDATE ON quote_snapshots
BEGIN SELECT RAISE(ABORT, 'quote_snapshots is append-only'); END;
CREATE TRIGGER IF NOT EXISTS quote_snapshots_no_delete BEFORE DELETE ON quote_snapshots
WHEN NOT (EXISTS (SELECT 1 FROM checkout_orders o WHERE o.id = OLD.order_id AND o.retain_until IS NOT NULL AND julianday(o.retain_until) <= julianday('now'))
  AND NOT EXISTS (SELECT 1 FROM checkout_holds h WHERE h.order_id = OLD.order_id AND h.released_at IS NULL))
BEGIN SELECT RAISE(ABORT, 'quote_snapshots are kept with their order'); END;

-- 15 · Messages PlotArt prepares for an order (the buyer's purchase confirmation): the exact text, fingerprinted, once
--      per order and kind; every delivery attempt is recorded separately. In test mode nothing leaves PlotArt: messages
--      go only to checkout_mail_sink.
CREATE TABLE IF NOT EXISTS order_messages (
  id             TEXT PRIMARY KEY,
  order_id       TEXT NOT NULL REFERENCES checkout_orders(id),
  kind           TEXT NOT NULL CHECK (kind IN ('buyer_confirmation','buyer_refund_pending','buyer_refund_failed','buyer_refund_reversed')),
  item_key       TEXT NOT NULL DEFAULT '',          -- e.g. the refund a notice is about: one notice per order, kind and refund
  recipient_role TEXT NOT NULL CHECK (recipient_role IN ('buyer','artist','founder')),
  subject        TEXT NOT NULL,
  body           TEXT NOT NULL,
  sha256         TEXT NOT NULL,
  created_at     TEXT NOT NULL,
  UNIQUE (order_id, kind, item_key)
);
CREATE TRIGGER IF NOT EXISTS order_messages_no_update BEFORE UPDATE ON order_messages
BEGIN SELECT RAISE(ABORT, 'order_messages is append-only'); END;
CREATE TABLE IF NOT EXISTS order_message_deliveries (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  message_id TEXT NOT NULL REFERENCES order_messages(id),
  order_id   TEXT NOT NULL,
  at         TEXT NOT NULL,
  channel    TEXT NOT NULL CHECK (channel IN ('test_sink','none','provider')),
  status     TEXT NOT NULL CHECK (status IN ('held_in_test_sink','not_sent_no_provider','accepted_by_provider','failed')),   -- 'accepted_by_provider' is not proof of inbox delivery
  detail     TEXT
);
CREATE TRIGGER IF NOT EXISTS order_message_deliveries_no_update BEFORE UPDATE ON order_message_deliveries
BEGIN SELECT RAISE(ABORT, 'order_message_deliveries is append-only'); END;
CREATE TABLE IF NOT EXISTS checkout_mail_sink (
  id         INTEGER PRIMARY KEY AUTOINCREMENT,
  at         TEXT NOT NULL,
  order_id   TEXT,
  kind       TEXT NOT NULL,
  to_role    TEXT NOT NULL,
  to_sha256  TEXT NOT NULL,                   -- the intended address is never stored here, only its fingerprint
  subject    TEXT NOT NULL,
  body       TEXT NOT NULL,
  delivery   TEXT NOT NULL DEFAULT 'held_in_test_sink' CHECK (delivery IN ('held_in_test_sink','accepted_by_provider','failed')),
  delivery_detail TEXT                           -- founder alerts are always recorded here (the alerts panel); if one was emailed, how that went
);

-- 16 · Amounts PlotArt owes artists (fee model B shortfalls; commission to return after a lost dispute, PA-GAA 9).
--      One row per item; the amount, rule and due date never change; settlement is recorded payment by payment.
CREATE TABLE IF NOT EXISTS checkout_owed (
  id              TEXT PRIMARY KEY,
  order_id        TEXT NOT NULL REFERENCES checkout_orders(id),
  kind            TEXT NOT NULL CHECK (kind IN ('processing_shortfall','commission_shortfall','lost_dispute_commission')),
  item_key        TEXT NOT NULL,
  cents           INTEGER NOT NULL CHECK (cents > 0),
  reason          TEXT NOT NULL,
  arisen_at       TEXT NOT NULL,
  due_at          TEXT NOT NULL,
  due_rule        TEXT NOT NULL,
  due_provisional INTEGER NOT NULL CHECK (due_provisional IN (0,1)),
  settled_cents   INTEGER NOT NULL DEFAULT 0 CHECK (settled_cents >= 0),
  reminders       TEXT,                       -- JSON: reminder stages already sent
  due_basis_event TEXT,                       -- PA-PAY 3.5 (sandbox rule, 18 Nov 2026): the record that first established the amount owed by bank transfer
  due_basis_at    TEXT,                       -- that record's time
  due_basis_date  TEXT,                       -- its Irish (Europe/Dublin) date; day one is the next day, due by the end of day 30
  due_basis_source TEXT CHECK (due_basis_source IS NULL OR due_basis_source IN ('stripe','pilot')),
  due_review      TEXT,                       -- why the founder should review the start date (uncertain time), if so
  last_return_id  TEXT,                       -- the returned transfer that last reduced settled_cents (see trigger)
  UNIQUE (order_id, item_key),
  CHECK (settled_cents <= cents)
);
CREATE INDEX IF NOT EXISTS checkout_owed_open ON checkout_owed(due_at) WHERE settled_cents < cents;
CREATE TRIGGER IF NOT EXISTS checkout_owed_fixed BEFORE UPDATE ON checkout_owed
WHEN NEW.cents <> OLD.cents OR NEW.kind <> OLD.kind OR NEW.due_at <> OLD.due_at OR NEW.order_id <> OLD.order_id
  OR NEW.due_basis_date IS NOT OLD.due_basis_date OR NEW.due_basis_at IS NOT OLD.due_basis_at OR NEW.due_basis_event IS NOT OLD.due_basis_event
  OR (NEW.settled_cents < OLD.settled_cents AND NOT (NEW.last_return_id IS NOT NULL AND NEW.last_return_id IS NOT OLD.last_return_id
      AND EXISTS (SELECT 1 FROM checkout_owed_payment_returns r WHERE r.id = NEW.last_return_id AND r.owed_id = OLD.id AND r.cents = OLD.settled_cents - NEW.settled_cents)))
BEGIN SELECT RAISE(ABORT, 'an owed amount, its rule and due date are fixed; settlement only increases, except by a recorded returned transfer'); END;
CREATE TABLE IF NOT EXISTS checkout_owed_payments (
  id          TEXT PRIMARY KEY,
  owed_id     TEXT NOT NULL REFERENCES checkout_owed(id),
  order_id    TEXT NOT NULL,
  cents       INTEGER NOT NULL CHECK (cents > 0),
  method      TEXT NOT NULL CHECK (method IN ('bank_transfer','stripe_application_fee_refund','moved_to_direct_payment')),
  reference   TEXT NOT NULL,                  -- transfer reference / fee refund id: never bank details
  executed_on TEXT,                           -- bank_transfer: the date PlotArt's bank shows the transfer as executed (YYYY-MM-DD)
  recorded_by TEXT NOT NULL,
  at          TEXT NOT NULL,
  UNIQUE (owed_id, reference),
  CHECK (method <> 'bank_transfer' OR executed_on GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]')
);
CREATE TRIGGER IF NOT EXISTS checkout_owed_payments_no_update BEFORE UPDATE ON checkout_owed_payments
BEGIN SELECT RAISE(ABORT, 'checkout_owed_payments is append-only'); END;
-- A bank transfer that came back: the outstanding amount is restored; the payment itself stays in the history.
-- Founder pause (18 Nov 2026): "Pause new quotes and payments" for absences. Append-only; the latest row is the current state.
CREATE TABLE IF NOT EXISTS checkout_pause_events (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  paused      INTEGER NOT NULL CHECK (paused IN (0,1)),
  return_on   TEXT CHECK (return_on IS NULL OR return_on GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'),
  note        TEXT CHECK (note IS NULL OR length(note) <= 300),
  by          TEXT NOT NULL,
  at          TEXT NOT NULL
);
CREATE TRIGGER IF NOT EXISTS checkout_pause_events_no_update BEFORE UPDATE ON checkout_pause_events
BEGIN SELECT RAISE(ABORT, 'checkout_pause_events is append-only'); END;
-- Founder alerts panel (18 Nov 2026): read state and the founder's next action for each founder alert in checkout_mail_sink.
-- Reading an alert never changes the underlying item: amounts stay outstanding until the issue itself is resolved.
CREATE TABLE IF NOT EXISTS checkout_founder_alert_reads (
  alert_id     INTEGER PRIMARY KEY REFERENCES checkout_mail_sink(id),
  order_id     TEXT,
  read_at      TEXT,
  read_by      TEXT,
  next_action  TEXT CHECK (next_action IS NULL OR length(next_action) <= 300),
  follow_up_on TEXT CHECK (follow_up_on IS NULL OR follow_up_on GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'),
  updated_at   TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS checkout_owed_payment_returns (
  id          TEXT PRIMARY KEY,
  payment_id  TEXT NOT NULL UNIQUE REFERENCES checkout_owed_payments(id),
  owed_id     TEXT NOT NULL REFERENCES checkout_owed(id),
  order_id    TEXT NOT NULL,
  cents       INTEGER NOT NULL CHECK (cents > 0),
  returned_on TEXT NOT NULL CHECK (returned_on GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'),
  reason      TEXT NOT NULL,
  recorded_by TEXT NOT NULL,
  at          TEXT NOT NULL
);
CREATE TRIGGER IF NOT EXISTS checkout_owed_payment_returns_no_update BEFORE UPDATE ON checkout_owed_payment_returns
BEGIN SELECT RAISE(ABORT, 'checkout_owed_payment_returns is append-only'); END;

-- PlotArt Studio · migration 0023 · Three galleries: the gallery data model (development 24 Nov 2026). NOT APPLIED IN PRODUCTION.
-- New tables only: gallery settings, memberships, artwork placements, unrestricted order, Artists in Focus per gallery, and the
-- per-use image consent requests and answers. See migrations/0023_three_galleries.sql and src/galleries.js.
CREATE TABLE IF NOT EXISTS gallery_settings (
  gallery_id TEXT PRIMARY KEY CHECK (gallery_id IN ('contemporary', 'environment', 'being')),
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
  gallery_id TEXT NOT NULL CHECK (gallery_id IN ('contemporary', 'environment', 'being')),
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
  gallery_id TEXT NOT NULL CHECK (gallery_id IN ('contemporary', 'environment', 'being')),
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
  gallery_id TEXT NOT NULL CHECK (gallery_id IN ('contemporary', 'environment', 'being')),
  position INTEGER NOT NULL CHECK (position >= 1 AND position <= 100000),
  artist_id TEXT NOT NULL REFERENCES artists(id) ON DELETE CASCADE,
  updated_at TEXT NOT NULL CHECK (length(updated_at) BETWEEN 20 AND 30),
  updated_by TEXT NOT NULL,
  PRIMARY KEY (gallery_id, position),
  UNIQUE (gallery_id, artist_id),
  CHECK (gallery_id <> 'contemporary' OR position >= 26)
);

CREATE TABLE IF NOT EXISTS gallery_features (
  gallery_id TEXT NOT NULL CHECK (gallery_id IN ('environment', 'being')),
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
  gallery_id TEXT CHECK (gallery_id IS NULL OR gallery_id IN ('contemporary', 'environment', 'being')),
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
  gallery_id TEXT CHECK (gallery_id IS NULL OR gallery_id IN ('contemporary', 'environment', 'being')),
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
