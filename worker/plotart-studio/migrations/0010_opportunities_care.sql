-- PlotArt Studio · migration 0010 · Opportunities & delivery: care condition and longer practical note (development 13 Nov 2026)
-- PROPOSAL FOR FOUNDER APPROVAL. NOT RUN against any real database.
-- Changes ONE table, artist_opportunities, and nothing else. It keeps every existing row and every existing column:
--   (1) a new column care_condition (0 or 1, default 0): "My interest depends on agreeing suitable care, handling and
--       insurance arrangements." Every existing answer starts unticked (0); only the artist can tick it;
--   (2) a new column practical_note (up to 2,000 characters), the longer replacement for note (up to 280);
--   (3) every existing note is COPIED into practical_note. The note column and its text are kept unchanged.
-- No row is added or removed, no other column changes, and no other table is touched. No trigger.
-- Why not rebuild the table: SQLite cannot widen a CHECK constraint in place, and a rebuild would drop and re-create the
-- table holding artists' answers. Adding columns and copying is the lower-risk change; the Studio reads the newest note
-- (note if an older Studio wrote one after this migration, otherwise practical_note) and from now on writes only
-- practical_note, clearing note.
-- Preconditions before anyone runs it:
--   (1) migration 0009 has run (it has: 13 Nov 2026);
--   (2) the founder has approved this exact file (SHA-256);
--   (3) it runs through studio-d1-migration, which takes a Time Travel restore point and an encrypted export first and
--       then checks that only artist_opportunities changed. Claude never runs it outside that workflow.
-- Run it ONCE: ADD COLUMN cannot be repeated (a second run is refused by the database and changes nothing).
-- @@DDL-BEGIN (schema.sql carries this block verbatim for new installs and local tests)

ALTER TABLE artist_opportunities ADD COLUMN care_condition INTEGER NOT NULL DEFAULT 0 CHECK (care_condition IN (0, 1));
ALTER TABLE artist_opportunities ADD COLUMN practical_note TEXT CHECK (practical_note IS NULL OR length(practical_note) <= 2000);
UPDATE artist_opportunities SET practical_note = note WHERE note IS NOT NULL AND practical_note IS NULL;

-- @@DDL-END

-- Rollback (separately approved, after a backup; removes only what this migration added; existing notes are untouched
-- in the note column, but notes longer than 280 characters written after this migration would be lost):
-- ALTER TABLE artist_opportunities DROP COLUMN practical_note;
-- ALTER TABLE artist_opportunities DROP COLUMN care_condition;
