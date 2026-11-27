-- PlotArt Studio · migration 0031 · open-ended Founding Artist numbers (development 27 Nov 2026).
-- The original Founding 25 wording, agreements, F25 application references and artists.founding_number values remain
-- untouched. New numbers above 25 live in this additive table so no existing artist row or contractual record is rewritten.

CREATE TABLE IF NOT EXISTS founding_artist_numbers (
  artist_id       TEXT PRIMARY KEY REFERENCES artists(id) ON DELETE CASCADE,
  founding_number INTEGER NOT NULL UNIQUE CHECK (founding_number BETWEEN 26 AND 999),
  assigned_by     TEXT NOT NULL,
  assigned_at     TEXT NOT NULL
);

-- A number above 25 is permanent while the artist record exists. Deletion can occur only through the existing artist
-- retention process, via ON DELETE CASCADE; an operational update is always refused.
CREATE TRIGGER IF NOT EXISTS founding_artist_numbers_no_update BEFORE UPDATE ON founding_artist_numbers
BEGIN SELECT RAISE(ABORT, 'a Founding Artist number never changes'); END;
