-- PlotArt Studio · migration 0009 · Opportunities & delivery (development 13 Nov 2026)
-- PROPOSAL FOR FOUNDER APPROVAL. NOT RUN against any real database.
-- Additive only: ONE new table and one index. No existing table, column, row, trigger, agreement, gallery, enquiry,
-- hire record or image permission is changed. It holds each artist's own EXPRESSION OF INTEREST in future opportunities,
-- where their artwork is based and how it could reach a venue. It enrols no one in anything and grants no permission.
-- No row for an artist means "not answered yet"; an artist who chose "Online gallery only for now" has a row saying so.
-- Preconditions before anyone runs it:
--   (1) a fresh D1 backup (studio-d1-backup or the migration workflow's own two backups);
--   (2) the founder has approved this exact file (SHA-256);
--   (3) it runs through studio-d1-migration with the founder's written approval. Claude never runs it.
-- Retention: the Studio deletes an artist's row with the first-stage deletion (12 months after participation ends, or
-- sooner on request) and, as a backstop, with the six-year deletion. ON DELETE CASCADE also removes it with the artist.
-- @@DDL-BEGIN (schema.sql carries this block verbatim for new installs and local tests)

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

-- @@DDL-END

-- Rollback (separately approved, after a backup; drops only what this migration created):
-- DROP TABLE IF EXISTS artist_opportunities;
