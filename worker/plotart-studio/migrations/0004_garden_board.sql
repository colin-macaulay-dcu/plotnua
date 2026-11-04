-- PlotNua · The Borrowed Garden noticeboard (migration 0004, MVP, founder decision 4 Nov 2026). NOT APPLIED ANYWHERE.
-- Three tables in the Studio's D1 database, alongside the Idea Board. Plain CREATE TABLE (not IF NOT EXISTS) so a
-- second run fails loudly instead of silently. The existing Airtable registers are NOT migrated here: those people
-- consented to a private register, not a public listing.
--
-- Public fields (published only after the founder approves): kind, county, area, space_type, availability,
-- description (or public_text when the founder tidied it), photo_key (an approved photograph), ref, published_at,
-- expires_at. PRIVATE fields (never published): contact_email, consent_at, decided_by, and the moderation times.
-- Unused monetisation fields (founder decision 4 Nov 2026: present, never set by any code path in the MVP):
-- account_type, listing_tier, featured_until, organisation_id. Every listing is free, individual and unfeatured, and
-- the noticeboard orders listings by date only.
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
