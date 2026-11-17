-- PlotArt Studio · migration 0016 · Homepage curation (development 17 Nov 2026)
-- PROPOSAL FOR FOUNDER APPROVAL. NOT RUN against any real database.
-- ADDITIVE: creates ONE new table, homepage_features, and nothing else. No existing table, row or column is touched; no
-- trigger. The table holds only the founder's homepage selection: up to six positions, each an artwork, or an artist
-- represented by one of their published artworks that the founder chooses (both kinds always name the artwork shown).
-- It never holds a price, availability, image, permission or anything an artist wrote.
-- What it can ever show is decided elsewhere: the Studio offers only works in an artist's latest PUBLISHED version, and the
-- website renders the homepage section only from published galleries (anything withdrawn or unpublished drops out).
-- Preconditions before anyone runs it:
--   (1) migrations up to 0015 have run;
--   (2) the founder has approved this exact file (SHA-256);
--   (3) it runs through studio-d1-migration (Time Travel restore point and encrypted export first, then the check that only
--       the declared table changed). Claude never runs it outside that workflow.
-- Re-running it is harmless (IF NOT EXISTS).
-- @@DDL-BEGIN (schema.sql carries this block verbatim for new installs and local tests)

CREATE TABLE IF NOT EXISTS homepage_features (
  position INTEGER PRIMARY KEY CHECK (position BETWEEN 1 AND 6),
  kind TEXT NOT NULL CHECK (kind IN ('artwork', 'artist')),
  artist_id TEXT NOT NULL REFERENCES artists(id),
  artwork_id TEXT NOT NULL REFERENCES artworks(id),
  updated_at TEXT NOT NULL CHECK (length(updated_at) BETWEEN 20 AND 30)
);

-- @@DDL-END

-- Rollback (separately approved): DROP TABLE homepage_features;  -- removes only the founder's homepage selection
