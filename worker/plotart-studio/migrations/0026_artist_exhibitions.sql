-- PlotArt Studio · migration 0026 · Exhibitions & Achievements (Phase C, development 25 Nov 2026)
-- PROPOSAL FOR FOUNDER APPROVAL. NOT RUN against any real database.
-- Changes ONE table, artists, by adding ONE column and nothing else:
--   exhibitions (text, optional, at most 6,000 characters): the artist's own Exhibitions & Achievements section, written
--   in PlotArt Studio and shown on their public gallery page after the biography once PlotArt has reviewed it.
-- Every existing artist starts with NULL (no section). Nothing is copied or moved from any biography: biographies stay
-- exactly as they are. No row is added, removed or otherwise changed, no other column or table is touched, and there is
-- no trigger. No agreement, licence, acceptance, gallery position, Founding number, gallery membership, artwork,
-- enquiry, payment or image record changes.
-- Numbering (founder instruction, 25 Nov 2026): 0024 is the Environment-to-Spaces change (Track A, on main) and 0025 is
-- artist location and delivery coverage (this track); this is 0026. It replaces an earlier, unreleased 0026 draft
-- (artist_achievements, a second implementation of the same section), which was withdrawn so that only the approved
-- implementation remains. None of 0024, 0025 or 0026 touches the same column.
-- Preconditions before anyone runs it:
--   (1) migrations 0024 and 0025 have run first (keeps the numbered history in order);
--   (2) the founder has approved this exact file (SHA-256);
--   (3) it runs through studio-d1-migration, which takes a Time Travel restore point and an encrypted export first and
--       then checks that only artists changed. Changing an existing table is never automatic: the founder approves the
--       run in GitHub (studio-database). Claude never runs it outside that workflow.
-- Run it ONCE: ADD COLUMN cannot be repeated (a second run is refused by the database and changes nothing).
-- Studio code that knows the column hides the editor and refuses the field until the column exists, so deploying the
-- Studio before or after this migration is safe either way.
-- @@DDL-BEGIN (schema.sql carries this block verbatim for new installs and local tests)

ALTER TABLE artists ADD COLUMN exhibitions TEXT CHECK (exhibitions IS NULL OR length(exhibitions) BETWEEN 1 AND 6000);

-- @@DDL-END

-- Rollback (separately approved, after a backup; removes only what this migration added). Older Studio code ignores
-- the column, so a Studio rollback alone does not need it:
-- ALTER TABLE artists DROP COLUMN exhibitions;
