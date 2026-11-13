-- PlotArt Studio · migration 0011 · Open for Commissions (development 13 Nov 2026)
-- PROPOSAL FOR FOUNDER APPROVAL. NOT RUN against any real database.
-- Changes ONE table, artists, by adding ONE column and nothing else:
--   open_for_commissions (0 or 1, default 0): the artist's own choice to show "Open for commissions" on their public
--   gallery page and to receive "Enquire about a commission" messages through the existing enquiry relay.
-- Every existing artist starts at 0 (off). Only the artist switches it, in PlotArt Studio. No row is added, removed or
-- otherwise changed, no other column or table is touched, and there is no trigger. No agreement, licence, acceptance,
-- gallery position, Founding number, artwork, enquiry or image record changes.
-- Numbering (founder instruction, 13 Nov 2026): 0010 (Opportunities care) is released and awaiting its own approved run;
-- this is 0011. The Gallery Artist Programme plan's artist_terms table moves to 0012 and PA-GAA installation to 0013.
-- Preconditions before anyone runs it:
--   (1) migration 0010 has run first (keeps the numbered history in order; the two touch different tables);
--   (2) the founder has approved this exact file (SHA-256);
--   (3) it runs through studio-d1-migration, which takes a Time Travel restore point and an encrypted export first and
--       then checks that only artists changed. Changing an existing table is never automatic: the founder approves the
--       run in GitHub (studio-database). Claude never runs it outside that workflow.
-- Run it ONCE: ADD COLUMN cannot be repeated (a second run is refused by the database and changes nothing).
-- @@DDL-BEGIN (schema.sql carries this block verbatim for new installs and local tests)

ALTER TABLE artists ADD COLUMN open_for_commissions INTEGER NOT NULL DEFAULT 0 CHECK (open_for_commissions IN (0, 1));

-- @@DDL-END

-- Rollback (separately approved, after a backup; removes only what this migration added). Older Studio code ignores
-- the column, so a Studio rollback alone does not need it:
-- ALTER TABLE artists DROP COLUMN open_for_commissions;
