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
  application_ref TEXT,
  created_at TEXT NOT NULL, updated_at TEXT NOT NULL
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
