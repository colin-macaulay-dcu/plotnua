-- PlotArt Studio · migration 0028 · Gallery Showcase (Report 37, development 26 Nov 2026)
-- PROPOSAL FOR FOUNDER APPROVAL. NOT RUN against any real database.
-- Adds ONE new table, gallery_showcase, and two refusal-only triggers on it. No existing table, row, column, consent,
-- agreement, gallery membership, placement, position, Artists in Focus selection or artwork changes.
--
-- What it holds: the three opening artworks of each gallery page (left 1, centre 2, right 3), chosen by the founder in
-- the Review Desk, kept as two separate stages:
--   draft      what the founder is preparing; saving it never publishes anything;
--   published  what the public page shows; changed only by the founder's explicit "Publish showcase".
-- A chosen artwork that stops being eligible (sold, withdrawn, unpublished, out of the gallery) is NOT removed or
-- replaced here: the record keeps the founder's choice, the public page leaves the place out, and the Review Desk names
-- the vacant position, the artwork and the reason until the founder chooses again.
--
-- The database itself refuses an artwork that does not belong to the named artist (BEFORE INSERT / UPDATE triggers;
-- artworks(id) alone is the primary key, so a composite foreign key is not available). Each artwork appears once per
-- gallery and stage.
--
-- Initial configuration: the three works the Contemporary page shows today (Night Garden, Foxgloves and Gorse, Energetic
-- Labyrinths 12), in the same order, as both draft and published, each only if that artwork exists.
--
-- Safe to run again: CREATE ... IF NOT EXISTS and INSERT OR IGNORE, so a second run changes nothing.
-- Preconditions: migrations up to 0027 have run; the founder has approved this exact file (SHA-256); it runs through
-- studio-d1-migration (Time Travel restore point and encrypted full backup first). It only adds a table (additive).
-- Compatibility: the live Studio never reads this table; the new Studio hides the Gallery Showcase until it exists.
-- @@DDL-BEGIN (schema.sql carries this block verbatim for new installs and local tests)

CREATE TABLE IF NOT EXISTS gallery_showcase (
  gallery_id TEXT NOT NULL CHECK (gallery_id IN ('contemporary', 'spaces', 'being')),
  stage TEXT NOT NULL CHECK (stage IN ('draft', 'published')),
  position INTEGER NOT NULL CHECK (position BETWEEN 1 AND 3),
  artist_id TEXT NOT NULL REFERENCES artists(id) ON DELETE CASCADE,
  artwork_id TEXT NOT NULL REFERENCES artworks(id) ON DELETE CASCADE,
  updated_at TEXT NOT NULL CHECK (length(updated_at) BETWEEN 20 AND 30),
  updated_by TEXT NOT NULL CHECK (length(updated_by) BETWEEN 3 AND 200),
  PRIMARY KEY (gallery_id, stage, position),
  UNIQUE (gallery_id, stage, artwork_id)
);
CREATE TRIGGER IF NOT EXISTS gallery_showcase_artist_insert BEFORE INSERT ON gallery_showcase
  WHEN NOT EXISTS (SELECT 1 FROM artworks WHERE id = NEW.artwork_id AND artist_id = NEW.artist_id)
  BEGIN SELECT RAISE(ABORT, 'gallery_showcase: the artwork does not belong to that artist'); END;
CREATE TRIGGER IF NOT EXISTS gallery_showcase_artist_update BEFORE UPDATE OF artist_id, artwork_id ON gallery_showcase
  WHEN NOT EXISTS (SELECT 1 FROM artworks WHERE id = NEW.artwork_id AND artist_id = NEW.artist_id)
  BEGIN SELECT RAISE(ABORT, 'gallery_showcase: the artwork does not belong to that artist'); END;
INSERT OR IGNORE INTO gallery_showcase (gallery_id, stage, position, artist_id, artwork_id, updated_at, updated_by)
  SELECT 'contemporary', s.stage, 1, w.artist_id, w.id, '2026-11-21T00:00:00.000Z', 'existing' FROM artworks w, (SELECT 'draft' AS stage UNION ALL SELECT 'published') s WHERE w.id = 'wg1by72jg3b';
INSERT OR IGNORE INTO gallery_showcase (gallery_id, stage, position, artist_id, artwork_id, updated_at, updated_by)
  SELECT 'contemporary', s.stage, 2, w.artist_id, w.id, '2026-11-21T00:00:00.000Z', 'existing' FROM artworks w, (SELECT 'draft' AS stage UNION ALL SELECT 'published') s WHERE w.id = 'wfhtcyurvgf';
INSERT OR IGNORE INTO gallery_showcase (gallery_id, stage, position, artist_id, artwork_id, updated_at, updated_by)
  SELECT 'contemporary', s.stage, 3, w.artist_id, w.id, '2026-11-21T00:00:00.000Z', 'existing' FROM artworks w, (SELECT 'draft' AS stage UNION ALL SELECT 'published') s WHERE w.id = 'w226r60hfsh';
