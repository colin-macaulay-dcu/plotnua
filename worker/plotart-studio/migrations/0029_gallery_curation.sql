-- PlotArt Studio · migration 0029 · Unified gallery curation (founder approval for development, 26 Nov 2026)
-- PROPOSAL FOR FOUNDER APPROVAL. NOT RUN against any real database.
-- Adds ONE new table, gallery_curation, and three refusal-only triggers on it. No existing table, row, column, consent,
-- agreement, gallery membership, placement, founding position (gallery_positions), gallery order, Gallery Showcase,
-- Artists in Focus selection (homepage_features, gallery_features) or artwork changes: those are only READ, once, to
-- set up the founder's current arrangement.
--
-- What it holds: positions 4 onwards of each gallery's single curated arrangement (positions 1-3, the opening row, stay
-- in gallery_showcase). One row per artist: the artist and, optionally, the representative artwork the founder chose
-- (NULL = the artist's first eligible published artwork). Two stages, like gallery_showcase:
--   draft      what the founder is preparing; saving it never publishes anything;
--   published  what the public page shows; changed only by the founder's explicit "Publish".
-- The Studio writes the draft (or published) rows of BOTH tables in one database batch, so a move between the opening row
-- and the rest is never half-saved.
--
-- The database itself refuses: an artwork that does not belong to the named artist (insert and update), and an artist
-- who already holds an opening-row place in the same gallery and stage (each artist appears once per gallery).
--
-- Initial configuration (each gallery and stage, only while that gallery and stage has no rows yet):
--   the artists the page shows today below the opening row, in today's order: the founding positions 01-25
--   (gallery_positions), then the later order (gallery_order, positions 26+); for Spaces and Being their own
--   gallery_order. Artists who hold an opening-row place in that stage are left out (they are shown once, above).
--   The six current Artists in Focus (homepage_features; for Spaces and Being, gallery_features) keep the artwork chosen
--   for them; everyone else starts with NULL (their first eligible published artwork, as the page shows today).
--   Published artists the order does not name are not added here: the page appends them at the end, as it does today.
--
-- Safe to run again: CREATE ... IF NOT EXISTS, and the set-up runs only for a gallery and stage with no rows.
-- Preconditions: migrations up to 0028 have run; the founder has approved this exact file (SHA-256); it runs through
-- studio-d1-migration (Time Travel restore point and encrypted full backup first). It only adds a table.
-- Compatibility: the live Studio never reads this table; the new Studio uses it only once it exists.
-- @@DDL-BEGIN (schema.sql carries this block verbatim for new installs and local tests)

CREATE TABLE IF NOT EXISTS gallery_curation (
  gallery_id TEXT NOT NULL CHECK (gallery_id IN ('contemporary', 'spaces', 'being')),
  stage TEXT NOT NULL CHECK (stage IN ('draft', 'published')),
  position INTEGER NOT NULL CHECK (position BETWEEN 4 AND 100000),
  artist_id TEXT NOT NULL REFERENCES artists(id) ON DELETE CASCADE,
  artwork_id TEXT REFERENCES artworks(id) ON DELETE SET NULL,
  updated_at TEXT NOT NULL CHECK (length(updated_at) BETWEEN 20 AND 30),
  updated_by TEXT NOT NULL CHECK (length(updated_by) BETWEEN 3 AND 200),
  PRIMARY KEY (gallery_id, stage, position),
  UNIQUE (gallery_id, stage, artist_id)
);
CREATE TRIGGER IF NOT EXISTS gallery_curation_artist_insert BEFORE INSERT ON gallery_curation
  WHEN NEW.artwork_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM artworks WHERE id = NEW.artwork_id AND artist_id = NEW.artist_id)
  BEGIN SELECT RAISE(ABORT, 'gallery_curation: the artwork does not belong to that artist'); END;
CREATE TRIGGER IF NOT EXISTS gallery_curation_artist_update BEFORE UPDATE OF artist_id, artwork_id ON gallery_curation
  WHEN NEW.artwork_id IS NOT NULL AND NOT EXISTS (SELECT 1 FROM artworks WHERE id = NEW.artwork_id AND artist_id = NEW.artist_id)
  BEGIN SELECT RAISE(ABORT, 'gallery_curation: the artwork does not belong to that artist'); END;
CREATE TRIGGER IF NOT EXISTS gallery_curation_once BEFORE INSERT ON gallery_curation
  WHEN EXISTS (SELECT 1 FROM gallery_showcase s WHERE s.gallery_id = NEW.gallery_id AND s.stage = NEW.stage AND s.artist_id = NEW.artist_id)
  BEGIN SELECT RAISE(ABORT, 'gallery_curation: that artist already holds an opening-row place in this gallery'); END;

INSERT INTO gallery_curation (gallery_id, stage, position, artist_id, artwork_id, updated_at, updated_by)
  SELECT 'contemporary', s.stage, 3 + ROW_NUMBER() OVER (PARTITION BY s.stage ORDER BY o.r), o.artist_id,
    (SELECT h.artwork_id FROM homepage_features h JOIN artworks w ON w.id = h.artwork_id AND w.artist_id = h.artist_id WHERE h.artist_id = o.artist_id ORDER BY h.position LIMIT 1),
    '2026-11-26T00:00:00.000Z', 'existing'
  FROM (SELECT 'draft' AS stage UNION ALL SELECT 'published') s,
    (SELECT artist_id, MIN(r) AS r FROM (
       SELECT artist_id, position AS r FROM gallery_positions WHERE artist_id IS NOT NULL
       UNION ALL SELECT artist_id, 1000000 + position FROM gallery_order WHERE gallery_id = 'contemporary') GROUP BY artist_id) o
  WHERE EXISTS (SELECT 1 FROM artists a WHERE a.id = o.artist_id)
    AND NOT EXISTS (SELECT 1 FROM gallery_showcase c WHERE c.gallery_id = 'contemporary' AND c.stage = s.stage AND c.artist_id = o.artist_id)
    AND NOT EXISTS (SELECT 1 FROM gallery_curation x WHERE x.gallery_id = 'contemporary' AND x.stage = s.stage);
INSERT INTO gallery_curation (gallery_id, stage, position, artist_id, artwork_id, updated_at, updated_by)
  SELECT o.gallery_id, s.stage, 3 + ROW_NUMBER() OVER (PARTITION BY o.gallery_id, s.stage ORDER BY o.position), o.artist_id,
    (SELECT f.artwork_id FROM gallery_features f JOIN artworks w ON w.id = f.artwork_id AND w.artist_id = f.artist_id WHERE f.gallery_id = o.gallery_id AND f.artist_id = o.artist_id LIMIT 1),
    '2026-11-26T00:00:00.000Z', 'existing'
  FROM (SELECT 'draft' AS stage UNION ALL SELECT 'published') s, gallery_order o
  WHERE o.gallery_id IN ('spaces', 'being')
    AND NOT EXISTS (SELECT 1 FROM gallery_showcase c WHERE c.gallery_id = o.gallery_id AND c.stage = s.stage AND c.artist_id = o.artist_id)
    AND NOT EXISTS (SELECT 1 FROM gallery_curation x WHERE x.gallery_id = o.gallery_id AND x.stage = s.stage);
