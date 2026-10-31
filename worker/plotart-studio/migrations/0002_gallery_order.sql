-- PlotArt Studio · migration 0002 · Gallery order and permanent Founding 25 numbers (founder decision 31 Oct 2026)
-- Apply ONCE to the production D1 database, with the founder's approval, BEFORE deploying the Worker that uses it:
--   npx wrangler d1 execute plotart-studio --remote --file=migrations/0002_gallery_order.sql
-- Additive only: one new column (empty for every existing artist), one new table, one index. No existing row changes.
ALTER TABLE artists ADD COLUMN founding_number INTEGER CHECK (founding_number IS NULL OR founding_number BETWEEN 1 AND 25);
CREATE TABLE IF NOT EXISTS gallery_positions (
  position INTEGER PRIMARY KEY CHECK (position BETWEEN 1 AND 25),
  artist_id TEXT UNIQUE REFERENCES artists(id),
  reserved INTEGER NOT NULL DEFAULT 0 CHECK (reserved IN (0, 1)),
  note TEXT,
  updated_at TEXT NOT NULL,
  CHECK ((reserved = 1 AND artist_id IS NULL) OR (reserved = 0 AND artist_id IS NOT NULL AND note IS NULL))
);
CREATE UNIQUE INDEX IF NOT EXISTS artists_founding_number ON artists(founding_number) WHERE founding_number IS NOT NULL;
-- Position 01 reserved (founder decision 31 Oct 2026). The private note (who it is reserved for) is added by the founder
-- in Studio, never here: this file is in a public repository.
INSERT OR IGNORE INTO gallery_positions (position, artist_id, reserved, note, updated_at) VALUES (1, NULL, 1, NULL, strftime('%Y-%m-%dT%H:%M:%fZ', 'now'));
