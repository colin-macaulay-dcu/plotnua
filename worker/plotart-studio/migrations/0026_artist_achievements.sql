-- PlotArt Studio · migration 0026 · Exhibitions & Achievements (Phase C, development 25 Nov 2026)
-- PROPOSAL FOR FOUNDER APPROVAL. NOT RUN against any real database.
-- Changes ONE table, artists, by adding ONE optional column and nothing else:
--   achievements (text, NULL = none): the artist's own free-form Exhibitions & Achievements section (headings, paragraphs and
--   lists, in the Studio's stored form; see src/achievements.js). Following Dave King's feedback, it is a separate section
--   from the statement, shown on the public profile only when the artist has written something, after founder review.
-- Every existing artist starts with NULL (no section). No row is added, removed or otherwise changed, no other column or
-- table is touched, and there is no trigger. No agreement, licence, gallery position, artwork, enquiry or image changes.
-- Preconditions: migration 0025 has run first (keeps the numbered history in order); the founder has approved this exact
-- file (SHA-256); it runs through studio-d1-migration (restore point and encrypted export first, then the check that only
-- artists changed). Changing an existing table is never automatic: the founder approves the run in GitHub (studio-database).
-- Run it ONCE: ADD COLUMN cannot be repeated (a second run is refused by the database and changes nothing).
-- @@DDL-BEGIN (schema.sql carries this block verbatim for new installs and local tests)

ALTER TABLE artists ADD COLUMN achievements TEXT CHECK (achievements IS NULL OR length(achievements) BETWEEN 1 AND 6000);

-- @@DDL-END

-- Rollback (separately approved, after a backup; removes only what this migration added). Older Studio code ignores the
-- column, so a Studio rollback alone does not need it:
-- ALTER TABLE artists DROP COLUMN achievements;
