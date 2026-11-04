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
